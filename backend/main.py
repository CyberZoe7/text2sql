from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from config import DB_URL, TEXT2SQL_API_URL, TEXT2SQL_API_TOKEN

app = FastAPI(
    title="基于Text2SQL的智能数据库查询系统",
    description="支持自然语言查询转换为SQL，执行查询并返回结果",
    version="1.0"
)

# 允许前端跨域请求（注意根据实际部署调整）
origins = [
    "http://localhost:8080",
    "http://10.135.11.183:8080",
    "https://localhost:8080",
    "https://10.135.11.183:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库连接
engine = create_engine(DB_URL)


# 定义登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str


# 定义注册请求模型
class RegisterRequest(BaseModel):
    username: str
    password: str


# 定义查询请求模型，新增 permission 字段
class QueryRequest(BaseModel):
    sentence: str
    permission: int


class ForgotPasswordRequest(BaseModel):
    username: str
    new_password: str


@app.post("/api/login")
async def login_user(login: LoginRequest):
    """
    接收用户名和密码，查询数据库中的用户表验证登录
    """
    try:
        with engine.connect() as conn:
            sql = text("SELECT 用户名, 权限 FROM 管理员信息 WHERE 用户名 = :username AND 密码 = :password")
            result = conn.execute(sql, {"username": login.username, "password": login.password}).fetchone()
            if result:
                return {
                    "success": True,
                    "permission": result.权限
                }
            else:
                return {"success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询错误: {str(e)}")


@app.post("/api/register")
async def register_user(reg: RegisterRequest):
    """
    接收用户名和密码，注册新用户
    """
    try:
        with engine.connect() as conn:
            sql_check = text("SELECT * FROM 管理员信息 WHERE 用户名 = :username")
            existing = conn.execute(sql_check, {"username": reg.username}).fetchone()
            if existing:
                return {"success": False, "detail": "用户名已存在"}

            sql_insert = text("INSERT INTO 管理员信息 (用户名, 密码) VALUES (:username, :password)")
            conn.execute(sql_insert, {"username": reg.username, "password": reg.password})
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@app.post("/api/forgot-password")
async def forgot_password(fp: ForgotPasswordRequest):
    """
    忘记密码功能：接收用户名和新密码，更新用户表中的密码
    """
    try:
        with engine.connect() as conn:
            sql_check = text("SELECT * FROM 管理员信息 WHERE 用户名 = :username")
            user = conn.execute(sql_check, {"username": fp.username}).fetchone()
            if not user:
                return {"success": False, "detail": "该用户名不存在"}

            sql_update = text("UPDATE 管理员信息 SET 密码 = :new_password WHERE 用户名 = :username")
            conn.execute(sql_update, {"new_password": fp.new_password, "username": fp.username})
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新密码失败: {str(e)}")


def get_sql_from_text(sentence: str) -> str:
    """
    调用外部 Text2SQL 接口将自然语言转换为 SQL 语句
    """
    # 固定补充语句，确保返回纯 SQL
    sentence2 = "(要保证你输出的sql是基于我的数据库的，并且你输出的sql要保证一定能执行不出错，你的输出sql语句将直接用于执行，请只给出sql语句不要说其他多余的话，只能输出可以直接执行的sql，不能有任何前缀，错误输出示例：sql：SELECT * FROM 产品，正确输出示例例如：SELECT * FROM 产品)"
    payload = {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "messages": [{
            "role": "user",
            "content": "你是一个MySQL专家，擅长Text2SQL。以下是我数据库的表，表名：部门（部门编号, 部门名称, 部门位置）；员工（员工编号, 姓名, 性别（男为M，女为F）, 出生日期, 联系电话, 电子邮件, 部门编号）；客户（客户编号, 客户名称, 联系人, 联系电话, 地址）；产品（产品编号, 产品名称, 产品描述, 单价, 库存数量）；订单（订单编号, 客户编号, 订单日期, 订单总额）；订单明细（明细编号, 订单编号, 产品编号, 数量, 单价）；供应商（供应商编号, 供应商名称, 联系人, 联系电话, 地址）；采购订单（采购订单编号, 供应商编号, 订单日期, 订单总额）；采购明细（明细编号, 采购订单编号, 产品编号, 数量, 单价）；管理员信息（管理员编号, 用户名, 密码, 权限），" + sentence + sentence2
        }],
        "stream": False,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1
    }
    headers = {
        "Authorization": f"Bearer {TEXT2SQL_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(TEXT2SQL_API_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="调用 Text2SQL 接口失败")
    data = response.json()
    sql_statement = data["choices"][0]["message"]["content"]
    # 保证返回的 SQL 格式正确（如存在替换情况，可根据实际情况做调整）
    sql_statement = sql_statement.replace("'商品信息表'", "商品信息表")
    return sql_statement


@app.post("/api/query")
def query_database(query: QueryRequest):
    """
    接收自然语言查询，将其转换为 SQL 并执行查询，返回 SQL 语句和查询结果。
    权限判断：
      - permission == 1 ：执行所有 SQL；
      - permission == 2 ：只允许查询产品表（表名 "产品"），如果 SQL 中引用了其他表则立即返回权限不足；
      - 其他权限：直接返回权限不足，无法查询。
    """
    # 先判断传入的权限是否为允许的值（1 或 2）
    if query.permission not in [1, 2]:
        raise HTTPException(status_code=403, detail="权限不足，无法查询")

    max_attempts = 3
    last_error = None

    for attempt in range(max_attempts):
        try:
            sql_statement = get_sql_from_text(query.sentence)

            # 如果权限为2，则只允许查询产品表，若 SQL 中引用了其他表，立即返回权限不足
            if query.permission == 2:
                allowed_table = "产品"
                tables = ["部门", "员工", "客户", "产品", "订单", "订单明细", "供应商", "采购订单", "采购明细", "管理员信息"]
                found_tables = [t for t in tables if t in sql_statement]
                if found_tables != [allowed_table]:
                    # 检查到权限不足时，直接返回，不进行重试
                    raise HTTPException(status_code=403, detail="权限不足，只允许查询产品表")

            # 使用 Pandas 执行 SQL 查询，得到 DataFrame
            df = pd.read_sql(sql_statement, engine)
            result = df.to_dict(orient="records")
            headers = df.columns.tolist()
            return {"sql": sql_statement, "headers": headers, "result": result}

        except HTTPException as he:
            # 权限错误直接返回，不再重试
            raise he
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt + 1} failed: {e}")

    raise HTTPException(status_code=500, detail=str(last_error))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="10.135.11.183",
        port=443,  # HTTPS 默认端口
        ssl_certfile="server.crt",  # 证书文件路径
        ssl_keyfile="server.key",  # 私钥文件路径
        reload=True
    )

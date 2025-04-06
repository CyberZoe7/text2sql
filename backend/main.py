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
    "http://10.135.38.13:8080",
    "https://localhost:8080",
    "https://10.135.38.13:8080"
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

# 定义查询请求模型（保留原有功能）
class QueryRequest(BaseModel):
    sentence: str

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
            # 使用参数化查询，防止SQL注入
            sql = text("SELECT * FROM 用户表 WHERE 用户名 = :username AND 密码 = :password")
            result = conn.execute(sql, {"username": login.username, "password": login.password}).fetchone()
            if result:
                return {"success": True}
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
            # 检查用户名是否已存在
            sql_check = text("SELECT * FROM 用户表 WHERE 用户名 = :username")
            existing = conn.execute(sql_check, {"username": reg.username}).fetchone()
            if existing:
                return {"success": False, "detail": "用户名已存在"}

            # 插入新用户记录
            sql_insert = text("INSERT INTO 用户表 (用户名, 密码) VALUES (:username, :password)")
            conn.execute(sql_insert, {"username": reg.username, "password": reg.password})
            conn.commit()  # 提交事务
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
            # 检查用户是否存在
            sql_check = text("SELECT * FROM 用户表 WHERE 用户名 = :username")
            user = conn.execute(sql_check, {"username": fp.username}).fetchone()
            if not user:
                return {"success": False, "detail": "该用户名不存在"}

            # 更新密码
            sql_update = text("UPDATE 用户表 SET 密码 = :new_password WHERE 用户名 = :username")
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
    sentence2 = "(请只给出sql语句不要说其他多余的话，只能输出这样的话例如：SELECT * FROM 商品信息表)"
    payload = {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "messages": [{
            "role": "user",
            "content": "以下是我数据库的表名：岗位信息表，顾客信息表，商品信息表，商品信息表中有列名分别为：商品名，单位价格，商品种类，所有的商品在商品信息表中，" + sentence + sentence2
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
    # 对返回的 SQL 做简单替换，确保表名格式正确
    sql_statement = sql_statement.replace("'商品信息表'", "商品信息表")
    return sql_statement

@app.post("/api/query")
def query_database(query: QueryRequest):
    """
    接收自然语言查询，将其转换为 SQL 并执行查询，返回 SQL 语句和查询结果
    """
    try:
        sql_statement = get_sql_from_text(query.sentence)
        # 使用 Pandas 执行 SQL 查询，得到 DataFrame
        df = pd.read_sql(sql_statement, engine)
        # 将 DataFrame 转换为字典格式返回
        result = df.to_dict(orient="records")
        # 获取真实的列名
        headers = df.columns.tolist()
        return {"sql": sql_statement, "headers": headers, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="10.135.38.13",
        port=443,  # HTTPS 的默认端口
        ssl_certfile="server.crt",  # 证书文件路径
        ssl_keyfile="server.key",   # 私钥文件路径
        reload=True
    )

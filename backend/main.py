import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from config import (DB_URL,TEXT2SQL_API_URL,TEXT2SQL_API_TOKEN,HOST_URL,SECRET_KEY,ALGORITHM,TOKEN_EXPIRE_HOURS)
import jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import re
# --- Bearer 认证实例 ---
security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    验证 Authorization: Bearer <token>，
    解码后返回 payload 中的 sub（用户名）和 permission。
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "username": payload.get("sub"),
            "permission": payload.get("permission")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token 已过期")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=403, detail=f"Token 验证失败:签名验证失败 {str(e)}")

# --- 创建 FastAPI 应用 ---
app = FastAPI(
    title="基于 Text2SQL 的智能数据库查询系统",
    description="支持自然语言查询→SQL，执行并返回结果",
    version="1.0"
)

# --- CORS 配置 ---
origins = [
    "http://localhost:8080",
    f"http://{HOST_URL}:8080",
    "https://localhost:8080",
    f"https://{HOST_URL}:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 初始化同步数据库引擎 ---
if not DB_URL:
    raise RuntimeError("config.py 中 DB_URL 未设置或为空，请检查")
engine = create_engine(DB_URL, pool_pre_ping=True)
# 在文件顶端定义你所有可查询的表名列表
TABLE_NAMES = [
    "部门", "员工", "客户", "产品",
    "订单", "订单明细", "供应商",
    "采购订单", "采购明细", "管理员信息"
]


# --- 请求模型定义 ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    secret_key: str      # 新增

class QueryRequest(BaseModel):
    sentence: str

class ForgotPasswordRequest(BaseModel):
    username: str
    secret_key: str      # 新增
    new_password: str

class ModifyPermissionRequest(BaseModel):
    username: str
    password: str
    secret_key: str

# --- 登录接口 ---
@app.post("/api/login")
async def login_user(login: LoginRequest):
    """
    接收用户名/密码，验证后发放 JWT。
    """
    try:
        with engine.connect() as conn:
            sql = text(
                "SELECT 用户名, 权限 FROM 管理员信息 "
                "WHERE 用户名 = :username AND 密码 = :password"
            )
            row = conn.execute(sql, {
                "username": login.username,
                "password": login.password
            }).fetchone()

        if not row:
            return {"success": False}

        # 构造 Payload 并签发 Token
        payload = {
            "sub": row.用户名,
            "permission": row.权限,
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "success": True,
            "username": row.用户名,
            "permission": row.权限,
            "token": token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询错误: {e}")

# --- 注册接口 ---
@app.post("/api/register")
async def register_user(reg: RegisterRequest):
    """
    接收用户名/密码/密钥，注册新管理员。
    如果同一密钥已在 管理员信息 表中被使用，则注册失败。
    """
    try:
        with engine.begin() as conn:
            # 1. 检查用户名是否已存在
            exists = conn.execute(
                text("SELECT 1 FROM 管理员信息 WHERE 用户名 = :username"),
                {"username": reg.username}
            ).fetchone()
            if exists:
                return {"success": False, "detail": "用户名已存在"}

            # 2. 检查密钥表中是否存在该密钥
            key_row = conn.execute(
                text("SELECT 权限 FROM 密钥表 WHERE 密钥 = :key"),
                {"key": reg.secret_key}
            ).fetchone()
            if not key_row:
                return {"success": False, "detail": "密钥不存在或已失效"}
            perm = key_row[0]

            # 3. 检查该密钥是否已被其他管理员使用
            used = conn.execute(
                text("SELECT 1 FROM 管理员信息 WHERE 密钥 = :key"),
                {"key": reg.secret_key}
            ).fetchone()
            if used:
                return {"success": False, "detail": "该密钥已被使用，无法重复注册"}

            # 4. 插入新用户，并把 permission 和 secret_key 一并存入管理员信息
            conn.execute(
                text(
                    "INSERT INTO 管理员信息 (用户名, 密码, 权限, 密钥) "
                    "VALUES (:username, :password, :permission, :secret_key)"
                ),
                {
                    "username": reg.username,
                    "password": reg.password,
                    "permission": perm,
                    "secret_key": reg.secret_key
                }
            )

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")

# --- 忘记密码接口 ---

@app.post("/api/forgot-password")
async def forgot_password(fp: ForgotPasswordRequest):
    """
    忘记密码：当 用户名+密钥 在 管理员信息 中匹配时，才更新密码。
    """
    try:
        with engine.begin() as conn:
            # 1. 检查用户+密钥是否匹配
            row = conn.execute(
                text(
                  "SELECT 1 FROM 管理员信息 "
                  "WHERE 用户名 = :username AND 密钥 = :secret_key"
                ),
                {"username": fp.username, "secret_key": fp.secret_key}
            ).fetchone()
            if not row:
                return {"success": False, "detail": "用户名或密钥不匹配"}

            # 2. 更新密码
            conn.execute(
                text(
                    "UPDATE 管理员信息 "
                    "SET 密码 = :new_password "
                    "WHERE 用户名 = :username"
                ),
                {"new_password": fp.new_password, "username": fp.username}
            )

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新密码失败: {e}")

# --- 文本转 SQL 辅助函数 ---
def get_sql_from_text(sentence: str) -> str:
    """
    调用外部 Text2SQL 接口，将自然语言转换为可执行 SQL。
    """
    try:
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            template = f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="prompt_template.txt 未找到")

    extra = (
        "。(请只输出可直接执行的 SQL，不要包含前缀、注释或代码块)"
    )
    full_prompt = f"{template}{sentence}{extra}"

    resp = requests.post(
        TEXT2SQL_API_URL,
        json={
            "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False,  # 非流式响应
            "max_tokens": 512,  # 限制输出长度
            "temperature": 0.7  # 控制随机性（0-1，值越高结果越多样）
        },
        headers={
            "Authorization": f"Bearer {TEXT2SQL_API_TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Text2SQL 接口调用失败")

    content = resp.json()["choices"][0]["message"]["content"]
    # 清洗返回内容
    for token in ["```", "sql", "SQL", "；"]:
        content = content.replace(token, "")

    return content.strip()


def get_suggestion_from_text(sentence: str) -> str:

    try:
        with open("prompt_template_2.txt", "r", encoding="utf-8") as f:
            template = f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="prompt_template_2.txt 未找到")


    full_prompt = f"{template}{sentence}"

    resp = requests.post(
        TEXT2SQL_API_URL,
        json={
            "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False,  # 非流式响应
            "max_tokens": 512,  # 限制输出长度
            "temperature": 0.7  # 控制随机性（0-1，值越高结果越多样）
        },
        headers={
            "Authorization": f"Bearer {TEXT2SQL_API_TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Text2SQL 接口调用失败")

    content = resp.json()["choices"][0]["message"]["content"]
    return content.strip()



# 定义允许的 SQL 操作关键字（仅 SELECT）
ALLOWED_KEYWORDS = ["SELECT"]
# --- 只允许 SELECT 且禁止其他关键字和分号 ---
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "EXEC", "MERGE", "CALL",
]
def validate_sql_operation(sql: str) -> None:
    """
    严格校验：
      1. 以 SELECT 开头
      2. 不包含分号或其他 DML/DDL 关键字
      3. SQL 中出现的表名都在白名单里
    """
    # 1. 以 SELECT 开头
    if not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
        raise HTTPException(403, "仅允许执行 SELECT 查询")

    # 2. 禁止出现任何分号或 FORBIDDEN_KEYWORDS
    upper_sql = sql.upper()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in upper_sql:
            raise HTTPException(403, f"SQL 中禁止使用关键字或符号：{kw}")

    # 3. 表名白名单：提取所有可能的表名 token 并逐一校验
    #    简化做法：只要 SQL 中出现的中文表名都得在白名单里
    for tbl in re.findall(r"\b([^\s,()]+)\b", sql):
        # 跳过 SELECT / FROM / WHERE / AND / OR /JOIN 等关键字
        if tbl in ("SELECT","FROM","WHERE","AND","OR","JOIN","ON",
                   "GROUP","BY","ORDER","HAVING","AS","INNER","LEFT","RIGHT"):
            continue
        # 如果它看起来像一个表名（在 TABLE_NAMES 中），跳过
        if tbl in TABLE_NAMES:
            continue
        # 如果它是一个字段名或别名，也无法区分，暂不校验
        # —— 此处只针对白名单之外的“疑似表名”抛错
        #    你可根据实际字段列表增加更精细的校验
        # continue

    # （可选）如果要更严格，可以解析 SQL AST 再校验。
# --- 查询接口（带权限控制） ---
@app.post("/api/query")
async def query_database(query: QueryRequest, token_payload: dict = Depends(verify_token)):
    """
    接收自然语言查询，进行智能提示或执行 SQL。
    如果 SQL 生成1次失败，则调用 get_suggestion_from_text 并返回提示。
    """
    sentence = query.sentence or ""
    low = sentence.lower()

    # 智能提示：有查询意图但没出现任何表名
    has_query_kw = any(k in low for k in ["查询", "查找", "select"])
    matched = [t for t in TABLE_NAMES if t in sentence]
    if has_query_kw and not matched:
        return {"suggestions": TABLE_NAMES}

    # 权限校验
    perm = token_payload["permission"]
    if perm not in (1, 2):
        raise HTTPException(403, "权限不足")

    max_attempts = 1# 尝试次数
    last_error = None

    for attempt in range(max_attempts):
        try:
            sql_statement = get_sql_from_text(sentence)
            validate_sql_operation(sql_statement)
            # 权限2只能查“产品”
            if perm == 2:
                if "产品" not in sql_statement:
                    raise HTTPException(403, "权限不足，只允许查询“产品”表")

            df = pd.read_sql(sql_statement, engine)
            return {
                "sql": sql_statement,
                "headers": df.columns.tolist(),
                "result": df.to_dict(orient="records")
            }

        except HTTPException:
            # 权限错误直接向上抛
            raise
        except Exception as e:
            last_error = e
            # 记录日志但继续重试
            print(f"[Text2SQL] Attempt {attempt+1} failed: {e}")

    # 三次转换均失败，调用智能提示
    try:
        suggestion_text = get_suggestion_from_text(sentence)
    except Exception as e:
        # 如果提示接口也出错，则返回最后一次错误
        raise HTTPException(status_code=500, detail=str(last_error))

    return {
        # 返回一条完整的提示文本，由前端专门展示
        "suggestionText": suggestion_text
    }
# --- 智能提示接口（单独调用） ---
@app.post("/api/suggestion")
async def get_suggestion(req: QueryRequest, token_payload: dict = Depends(verify_token)):
    """
    单独请求智能提示：调用 get_suggestion_from_text，将提示文本返回给前端。
    """
    sentence = req.sentence or ""
    # 权限校验，可按需调整：
    perm = token_payload["permission"]
    if perm not in (1, 2):
        raise HTTPException(403, "权限不足")

    try:
        suggestion_text = get_suggestion_from_text(sentence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能提示失败：{e}")

    return {"suggestion": suggestion_text}


@app.post("/api/modify-permission")
async def modify_permission(req: ModifyPermissionRequest):
    """
    用户凭原用户名+密码，以及新密钥来修改自己的权限。
    如果新密钥已被任何管理员使用，则修改失败。
    """
    try:
        with engine.begin() as conn:
            # 1. 验证用户名密码
            auth = conn.execute(
                text("SELECT 密码 FROM 管理员信息 WHERE 用户名 = :username"),
                {"username": req.username}
            ).fetchone()
            if not auth or auth[0] != req.password:
                return {"success": False, "detail": "用户名或密码错误"}

            # 2. 查新密钥对应权限
            key_row = conn.execute(
                text("SELECT 权限 FROM 密钥表 WHERE 密钥 = :key"),
                {"key": req.secret_key}
            ).fetchone()
            if not key_row:
                return {"success": False, "detail": "密钥不存在或已失效"}
            new_perm = key_row[0]

            # 3. 检查该密钥是否已被其他管理员使用
            used = conn.execute(
                text("SELECT 1 FROM 管理员信息 WHERE 密钥 = :key"),
                {"key": req.secret_key}
            ).fetchone()
            if used:
                return {"success": False, "detail": "该密钥已被使用，无法重复使用"}

            # 4. 更新管理员信息中的 权限 & 密钥
            conn.execute(
                text(
                  "UPDATE 管理员信息 "
                  "SET 权限 = :perm, 密钥 = :key "
                  "WHERE 用户名 = :username"
                ),
                {"perm": new_perm, "key": req.secret_key, "username": req.username}
            )

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改权限失败: {e}")


# --- 启动 Uvicorn ---
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST_URL,
        port=443,
        ssl_certfile="server.crt",
        ssl_keyfile="server.key",
        reload=True

    )

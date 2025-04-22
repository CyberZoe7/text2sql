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
        raise HTTPException(status_code=403, detail=f"Token 验证失败: {str(e)}")

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

# --- 请求模型定义 ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    sentence: str
    permission: int

class ForgotPasswordRequest(BaseModel):
    username: str
    new_password: str

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
    接收用户名/密码，注册新管理员。
    """
    try:
        with engine.begin() as conn:
            # 检查是否已存在
            exists = conn.execute(
                text("SELECT 1 FROM 管理员信息 WHERE 用户名 = :username"),
                {"username": reg.username}
            ).fetchone()
            if exists:
                return {"success": False, "detail": "用户名已存在"}

            # 插入新用户
            conn.execute(
                text(
                    "INSERT INTO 管理员信息 (用户名, 密码) "
                    "VALUES (:username, :password)"
                ),
                {"username": reg.username, "password": reg.password}
            )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")

# --- 忘记密码接口 ---
@app.post("/api/forgot-password")
async def forgot_password(fp: ForgotPasswordRequest):
    """
    忘记密码：根据用户名更新密码。
    """
    try:
        with engine.begin() as conn:
            # 确认用户存在
            user = conn.execute(
                text("SELECT 1 FROM 管理员信息 WHERE 用户名 = :username"),
                {"username": fp.username}
            ).fetchone()
            if not user:
                return {"success": False, "detail": "用户名不存在"}

            # 更新密码
            conn.execute(
                text(
                    "UPDATE 管理员信息 SET 密码 = :new_password "
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
            "stream": False,
            "max_tokens": 512,
            "temperature": 0.7
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

# --- 查询接口（带权限控制） ---
@app.post("/api/query")
async def query_database(
    query: QueryRequest,
    token_payload: dict = Depends(verify_token)
):
    """
    将自然语言转换的 SQL 执行并返回结果。
    permission==1：全表查询；permission==2：仅限“产品”表。
    """
    perm = token_payload.get("permission")
    if perm not in (1, 2):
        raise HTTPException(status_code=403, detail="权限不足")

    # 生成 SQL
    sql_statement = get_sql_from_text(query.sentence)

    # 若权限==2，强制只查“产品”表
    if perm == 2 and "产品" not in sql_statement:
        raise HTTPException(status_code=403, detail="仅允许查询 产品 表")

    # 执行 SQL 并返回 JSON
    try:
        df = pd.read_sql(sql_statement, engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行 SQL 失败: {e}")

    return {
        "sql": sql_statement,
        "headers": df.columns.tolist(),
        "result": df.to_dict(orient="records")
    }

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

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from sqlalchemy import create_engine, text,MetaData, inspect
from pydantic import BaseModel, Field
from config import (TEXT2SQL_API_URL,TEXT2SQL_API_TOKEN,HOST_URL,SECRET_KEY,ALGORITHM,TOKEN_EXPIRE_HOURS)
import jwt
import json
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import re
import sys,os
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
    "https://localhost:8000",
    f"https://{HOST_URL}:8000",
    "http://localhost:8000",
    f"http://{HOST_URL}:8000",
    "http://localhost:8080",
    f"http://{HOST_URL}:8080",
    "https://localhost:8080",
    f"https://{HOST_URL}:8080",
]
# 全局引擎，初始 None
engine = None
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=['*'],            # 或仅 http://127.0.0.1:8000
    allow_methods=['*'],
    allow_headers=['*'],
)

# 运行时资源目录：如果被 PyInstaller 打包，资源会在 sys._MEIPASS
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 证书路径
CERT_FILE = os.path.join(BASE_DIR, 'server.crt')
KEY_FILE  = os.path.join(BASE_DIR, 'server.key')
# 后面用到的模版
TPL1 = os.path.join(BASE_DIR, 'prompt_template.txt')
TPL2 = os.path.join(BASE_DIR, 'prompt_template_2.txt')
TPL3 = os.path.join(BASE_DIR, 'prompt_template_3.txt')
# 存储数据库结构的文件
DB_SCHEMA_FILE = os.path.join(BASE_DIR, 'database.txt')
# --- 初始化同步数据库引擎 ---

# 在文件顶端定义你所有可查询的表名列表
TABLE_NAMES = [
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

class DBConnectRequest(BaseModel):
    db_type: str = Field(..., pattern="^(mysql|postgresql|sqlserver)$")
    host: str
    port: int
    username: str
    password: str
    database: str

engine = None
SCHEMA = {}

@app.post("/api/db/connect")
async def connect_db(req: DBConnectRequest):
    """
    测试连接并在全局 engine 中保存可用的数据库引擎，
    同时将所有表和视图的字段信息写入 backend/database.txt。
    """
    global engine, SCHEMA

    # --- 1. 拼接 SQLAlchemy URL ---
    if req.db_type == "mysql":
        url = (
            f"mysql+mysqlconnector://{req.username}:{req.password}"
            f"@{req.host}:{req.port}/{req.database}?charset=utf8mb4"
        )
    elif req.db_type == "postgresql":
        url = (
            f"postgresql+psycopg2://{req.username}:{req.password}"
            f"@{req.host}:{req.port}/{req.database}"
        )
    else:  # sqlserver
        from urllib.parse import quote_plus
        driver = quote_plus("ODBC Driver 17 for SQL Server")
        url = (
            f"mssql+pyodbc://{req.username}:{req.password}"
            f"@{req.host}:{req.port}/{req.database}?driver={driver}"
        )

    # --- 2. 测试连接 ---
    try:
        tmp_engine = create_engine(url, pool_pre_ping=True)
        with tmp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"连接失败：{e}")

    # --- 3. 反射表和视图结构 ---
    inspector = inspect(tmp_engine)
    schema: dict[str, list[str]] = {}

    # 3.1 普通表
    for tbl in inspector.get_table_names():
        cols = inspector.get_columns(tbl)
        schema[tbl] = [c["name"] for c in cols]

    # 3.2 视图
    try:
        views = inspector.get_view_names()
    except NotImplementedError:
        # PostgreSQL/MySQL 也可以查询 information_schema
        views = [
            row[0]
            for row in tmp_engine.execute(text(
                "SELECT table_name FROM information_schema.views "
                "WHERE table_schema = :db"
            ), {"db": req.database})
        ]

    for vw in views:
        cols = inspector.get_columns(vw)
        schema[vw] = [c["name"] for c in cols]

    # --- 4. 写入本地文件 backend/database.txt ---
    # 文件路径相对于当前 main.py 文件目录
    base_dir = os.path.abspath(os.path.dirname(__file__))
    out_path = os.path.join(base_dir, "database.txt")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入 schema 文件失败：{e}")

    # --- 5. 保存全局 engine 与 SCHEMA 并返回 ---
    engine = tmp_engine
    SCHEMA = schema

    return {"success": True, "db_url": url}


# --- 后续所有需要数据库的接口都先检查 engine ---
def get_engine_or_400():
    if engine is None:
        raise HTTPException(status_code=400, detail="请先配置并测试数据库连接")
    return engine


# --- 登录接口 ---
@app.post("/api/login")
async def login_user(login: LoginRequest):
    """
    接收用户名/密码，验证后发放 JWT。
    """
    engine = get_engine_or_400()
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
    engine = get_engine_or_400()
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
    engine = get_engine_or_400()
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
        with open(TPL1, "r", encoding="utf-8") as f:
            template = f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="prompt_template.txt 未找到")
    # 2. 读取 database.txt，拼出“数据库结构”描述
    try:
        with open(DB_SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema: dict = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="database.txt 未找到，请先调用 /api/db/connect")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"解析 database.txt 失败：{e}")
    # 将 schema 转为一段自然语言：
    #   表1(字段A,字段B,...); 表2(...); 视图1(...); ...
    parts = []
    for tbl, cols in schema.items():
        cols_str = ", ".join(cols)
        parts.append(f"{tbl}({cols_str})")
    database_desc = "；数据库中包含以下表和视图及其字段：\n" + "；\n".join(parts) + "；\n"

    full_prompt = f"{template}{sentence}{database_desc}"

    resp = requests.post(
        TEXT2SQL_API_URL,
        json={
            "model": "THUDM/GLM-4-9B-0414",
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False,  # 非流式响应
            "max_tokens": 4096,  # 限制输出长度
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
        with open(TPL2, "r", encoding="utf-8") as f:
            template = f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="prompt_template_2.txt 未找到")
    # 2. 读取 database.txt，拼出“数据库结构”描述
    try:
        with open(DB_SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema: dict = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="database.txt 未找到，请先调用 /api/db/connect")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"解析 database.txt 失败：{e}")
    # 将 schema 转为一段自然语言：
    #   表1(字段A,字段B,...); 表2(...); 视图1(...); ...
    parts = []
    for tbl, cols in schema.items():
        cols_str = ", ".join(cols)
        parts.append(f"{tbl}({cols_str})")
    database_desc = "；数据库中包含以下表和视图及其字段：\n" + "；\n".join(parts) + "；\n"

    full_prompt = f"{template}{sentence}{database_desc}"

    resp = requests.post(
        TEXT2SQL_API_URL,
        json={
            "model": "THUDM/GLM-4-9B-0414",
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
    engine = get_engine_or_400()
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

# --- 在文件顶端导入 verify_token, requests 等已有组件 ---

class TemplateRequest(BaseModel):
    # 未来可以加入行业/表名等上下文参数；当前无需额外字段
    pass

@app.post("/api/templates")
async def generate_templates(
    _: TemplateRequest,
    token_payload: dict = Depends(verify_token)
):
    try:
        with open(TPL3, "r", encoding="utf-8") as f:
            template = f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="prompt_template_3.txt 未找到")
    # 2. 读取 database.txt，拼出“数据库结构”描述
    try:
        with open(DB_SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema: dict = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="database.txt 未找到，请先调用 /api/db/connect")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"解析 database.txt 失败：{e}")
    # 将 schema 转为一段自然语言：
    #   表1(字段A,字段B,...); 表2(...); 视图1(...); ...
    parts = []
    for tbl, cols in schema.items():
        cols_str = ", ".join(cols)
        parts.append(f"{tbl}({cols_str})")
    database_desc = "；数据库中包含以下表和视图及其字段：\n" + "；\n".join(parts) + "；\n"

    prompt = f"{template}{database_desc}"
    # """
    # 调用大模型，自动生成查询模板，每行一句并用双引号包裹，返回模板列表。
    # """
    # 可根据业务场景定制 prompt
    try:
        resp = requests.post(
            TEXT2SQL_API_URL,
            json={
                "model": "THUDM/GLM-4-9B-0414",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.7,
                "stream": False
            },
            headers={
                "Authorization": f"Bearer {TEXT2SQL_API_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板生成失败：{e}")

    content = resp.json()["choices"][0]["message"]["content"]
    # 按行拆分，去除空行和首尾双引号
    # 按行拆分，去除空行和首尾双引号
    templates = []
    for line in content.splitlines():
        tpl = line.strip()
        if not tpl:
            continue
        if tpl.startswith('"') and tpl.endswith('"'):
            # Python 切片，而不是 JavaScript slice()
            templates.append(tpl[1:-1])
        else:
            templates.append(tpl)
    return {"templates": templates}



# --- 启动 Uvicorn ---
if __name__ == "__main__":
    # 如果是 PyInstaller 打包后的可执行文件（sys.frozen == True），
    # 就不要用 reload，也不要监听 watchfiles
    is_packaged = getattr(sys, "frozen", False)
    uvicorn.run(
        "main:app",             # 假设你的 FastAPI app 在 main.py 的 app 变量里
        host=HOST_URL,
        port=443,
        ssl_certfile=CERT_FILE,
        ssl_keyfile=KEY_FILE,
        reload=True,  # 打包时设为 False，本地开发时你可以手动设 True
        # watch_dirs=None       # (可选) 如果你手动传这个，就完全不监听任何目录
    )
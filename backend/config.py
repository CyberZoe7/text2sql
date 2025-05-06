# backend/config.py
import json
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta

# —— 1. 基本配置 —— #
DB_URL = "mysql+mysqlconnector://root:hqm111222333@localhost/小型企业数据库"
TEXT2SQL_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
TEXT2SQL_API_TOKEN = "sk-dguldiyzvpupvknhgyvyxnrhtguktyzjmvvjbbzbbedfygvk"
HOST_URL = "10.135.8.214"

# —— 2. 密钥存储文件 —— #
BASE_DIR = Path(__file__).parent
SECRET_FILE = BASE_DIR / "secret_store.json"

# —— 3. 默认值 —— #
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 6

def _current_utc_iso():
    return datetime.now(timezone.utc).isoformat()

# 首次写入时用到的模板
_TEMPLATE = {
    "secret_key": secrets.token_urlsafe(32),
    "algorithm": ALGORITHM,
    "expire_hours": TOKEN_EXPIRE_HOURS,
    "last_rotated": _current_utc_iso(),
}

def _write_secrets(data: dict):
    SECRET_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # POSIX 下锁定权限为 600
    if os.name == "posix":
        try:
            os.chmod(SECRET_FILE, 0o600)
        except Exception:
            pass

def _load_or_init_file():
    """
    确保 secret_store.json 存在且结构完整，
    否则初始化为 _TEMPLATE。
    """
    if not SECRET_FILE.exists():
        _write_secrets(_TEMPLATE)
        return _TEMPLATE.copy()

    # 读的时候自动去 BOM
    try:
        raw = SECRET_FILE.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        # 文件损坏，重建
        SECRET_FILE.unlink(missing_ok=True)
        _write_secrets(_TEMPLATE)
        return _TEMPLATE.copy()

    # 如果缺少某些字段，也重建
    for key in _TEMPLATE:
        if key not in data:
            data = _TEMPLATE.copy()
            _write_secrets(data)
            break
    return data

def get_secret_key() -> str:
    """
    每次调用都会检查是否超过 expire_hours，
    超过则自动 rotation 并持久化。
    """
    data = _load_or_init_file()

    # 上次旋转时间
    last = datetime.fromisoformat(data["last_rotated"])
    now = datetime.now(timezone.utc)
    if now - last >= timedelta(hours=data["expire_hours"]):
        # 超过周期，重新生成
        data["secret_key"] = secrets.token_urlsafe(32)
        data["last_rotated"] = _current_utc_iso()
        _write_secrets(data)

    return data["secret_key"]


# —— 直接从文件加载不带检测的副本（仅供引用默认值） —— #
_secrets = _load_or_init_file()

# —— 导出给外部使用 —— #
# 注意：真正签发/校验 JWT 时，请调用 get_secret_key()
SECRET_KEY =  get_secret_key()
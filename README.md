# Text2SQL 智能数据库查询系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个基于 **Vue 3** 前端 + **FastAPI** 后端 + **Text2SQL** 转换的智能查询系统，支持：
- 自然语言 → 可执行 SQL  
- 用户注册／JWT 登录鉴权  
- 权限控制（全表／仅“产品”表）  
- 智能提示：缺表名时返回候选表列表  
- 常用查询模板引导  
- 导出 Excel  
- 图表可视化（折线、柱状、饼图）  

---

## 🚀 核心功能

1. **自然语言转 SQL**  
   - 将中文或英文查询意图，调用第三方 Text2SQL 接口，生成纯粹可执行的 SQL。  
2. **注册 / JWT 登录**  
   - `/api/register` 注册新管理员  
   - `/api/login` 校验后发放带权限的 JWT  
3. **权限控制**  
   - 权限 1：可查询所有表  
   - 权限 2：仅可查询 “产品” 表，其他表请求被拒绝  
4. **智能提示**  
   - 若句中含“查询”“查找”等关键词但不含任何已知表名，后端返回所有表名列表供候选  
5. **查询模板**  
   - 首页展示常用 SQL 模板，一键填充降低学习成本  
6. **导出 Excel**  
   - 将查询结果一键导出为 `.xlsx`  
7. **图表可视化**  
   - 支持折线图、柱状图、饼图，根据用户选字段动态渲染  

---

## ⚙️ 技术栈

- **前端**  
  - Vue 3 + Composition API  
  - Vue Router  
  - Axios  
  - XLSX.js （导出 Excel）  
  - Chart.js （图表可视化）  

- **后端**  
  - Python 3.8+  
  - FastAPI + Uvicorn  
  - SQLAlchemy + mysql-connector-python  
  - pandas  
  - PyJWT（JWT 鉴权）  
  - requests（调用 Text2SQL 接口）  

- **第 三 方 Text2SQL**  
  - DeepSeek-R1-Distill-Qwen-7B 模型  

---

## 🚀 快速启动

### 克隆仓库

```bash
git clone https://github.com/CyberZoe7/text2sql.git
cd text2sql

后端部署
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
编辑 backend/config.py，设置：
DB_URL = "mysql+mysqlconnector://<db_user>:<db_pass>@<db_host>/<db_name>"
TEXT2SQL_API_TOKEN = "<你的 Text2SQL 服务令牌>"
HOST_URL = "<后端主机地址或 IP>"
首次启动时会自动生成 secret_store.json 保存随机的 SECRET_KEY，并设为 600 权限。

前端部署
cd ../frontend
npm install
配置
编辑 frontend/src/api.js，将 BASE_URL 指向你的后端地址，例如：
export const BASE_URL = "https://<YOUR_HOST>:8000";
export const LOGIN_URL = `${BASE_URL}/api/login`;
export const QUERY_URL = `${BASE_URL}/api/query`;
运行
npm run serve
打开浏览器访问 http://localhost:8080

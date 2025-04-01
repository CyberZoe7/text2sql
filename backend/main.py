from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
from sqlalchemy import create_engine
from pydantic import BaseModel
from config import DB_URL, TEXT2SQL_API_URL, TEXT2SQL_API_TOKEN

app = FastAPI(
    title="基于Text2SQL的智能数据库查询系统",
    description="支持自然语言查询转换为SQL，执行查询并返回结果",
    version="1.0"
)

# 允许前端跨域请求（注意根据实际部署调整）
origins = [
    "http://localhost:8081",
    "http://10.135.9.41:8081"
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

# 定义请求模型
class QueryRequest(BaseModel):
    sentence: str

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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import re

app = FastAPI()

DB_FILE = "data.db"

class QueryRequest(BaseModel):
    sql: str

def clean_sql(raw_sql: str) -> str:
    """LLMが返しがちな ```sql ... ``` などのマークダウン装飾を除去する"""
    text = raw_sql.strip()
    # 先頭と末尾のコードブロック記号を削除
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

@app.post("/query")
def query_db(req: QueryRequest):
    sql = clean_sql(req.sql)

    if not sql:
        raise HTTPException(status_code=400, detail="SQL query cannot be empty")

    # SELECT / WITH のみ許可
    first_word = sql.split()[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT or WITH queries are allowed"
        )

    conn = None
    try:
        # URIモードで完全読み取り専用（mode=ro）で接続
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]

        return {
            "count": len(result),
            "rows": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Database error: {str(e)}"
        )
    finally:
        # エラー発生時でも確実に接続を閉じる
        if conn:
            conn.close()
from datetime import datetime
import sqlite3
import requests
import re
import os

os.environ["NO_PROXY"] = "*"  # 社内通信でプロキシを経由させない設定

# Dify設定
DIFY_BASE_URL = "http://service.test.dify.blue.dev01.local/v1"
API_KEY_SQL = "app-VUr7d7TYRrFOml6bBESTlevP"       # アプリ1のAPIキー
API_KEY_ANALYST = "app-WV5pK4YaXRD01gyu99kXZA4d"   # アプリ2のAPIキー
DB_PATH = "./db/large_data.db"
HISTORY_FILE = "analysis_history.md"

def save_history(query, sql, answer):
  """質問と回答の履歴をMarkdownファイルへ追記保存する"""
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  with open(HISTORY_FILE, "a", encoding="utf-8") as f:
    f.write(f"## 実行日時: {now}\n")
    f.write(f"**質問:** {query}\n\n")
    f.write(f"**実行SQL:**\n```sql\n{sql}\n```\n\n")
    f.write(f"**回答:**\n{answer}\n\n")
    f.write("-" * 40 + "\n\n")

def call_dify_api(api_key, inputs):
    url = f"{DIFY_BASE_URL}/workflows/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": "local-dev-user"
    }
    
    session = requests.Session()
    session.trust_env = False
    
    res = session.post(url, headers=headers, json=payload)
    res.raise_for_status()
    
    res_json = res.json()
    data = res_json.get("data", {})
    
    # Difyワークフロー側でエラーが発生している場合
    if data.get("status") == "failed":
        print(f"\n[Difyエラー] ワークフロー実行に失敗しました: {data.get('error')}")
        return ""
        
    outputs = data.get("outputs", {})
    
    # 出力変数(outputs)が空の場合
    if not outputs:
        print(f"\n[Difyエラー] 出力データが空です。APIレスポンス: {res_json}")
        return ""
    
    # 'result' キーがあればそれを使い、なければ最初の出力変数を動的に取得
    if "result" in outputs:
        return outputs["result"]
    else:
        return list(outputs.values())[0]

def run_analysis(user_query):
    """ユーザーの質問をもとに SQL生成 -> DB実行 -> 回答生成 を行う"""
    print(f"\n--- 質問処理中: 「{user_query}」 ---")
    # 1. DifyでSQL文を生成
    raw_sql = call_dify_api(API_KEY_SQL, {"query": user_query})
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", raw_sql.strip(), flags=re.IGNORECASE)
    
    # --- SQLが空の場合はここで安全に中断 ---
    if not sql:
        print("[エラー] SQLの生成に失敗しました。Difyのアプリ1の終了ノード設定と公開状態を確認してください。")
        return
        
    print(f"\n[生成されたSQL]\n{sql}\n")
    
    # 2. ローカルSQLiteで高速実行（数百万行でも一瞬で完了）
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    print(f"■ 取得データ件数: {len(rows)}件")
    
    # 3. 実行結果をDifyに渡して最終回答を生成（トークン数考慮で最大100件）
    final_answer = call_dify_api(API_KEY_ANALYST, {
        "query": user_query,
        "data": str(rows[:100])
    })
    
    print("\n================== 分析結果 ==================")
    print(final_answer)

    # 4. 履歴をファイルへ自動保存
    save_history(user_query, sql, final_answer)
    print(f"※ 実行結果を '{HISTORY_FILE}' に保存しました。")

if __name__ == "__main__":
    print("==============================================")
    print("      Dify データ分析アシスタント起動         ")
    print("  ※ 終了したい場合は 'q' または 'exit' と入力   ")
    print("==============================================\n")
    
    while True:
        try:
            # ユーザーからの入力受付
            user_input = input("質問を入力してください > ").strip()
            
            # 終了判定
            if user_input.lower() in ["q", "exit", "quit", "終了"]:
                print("プログラムを終了します。")
                break
                
            # 空入力のスキップ
            if not user_input:
                continue
                
            # 分析処理の実行
            run_analysis(user_input)
            
        except KeyboardInterrupt:
            # Ctrl+C が押された場合も安全に終了
            print("\n中断されました。プログラムを終了します。")
            break
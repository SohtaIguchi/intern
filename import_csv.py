import sqlite3
import pandas as pd

# 【テーブル名: (CSVファイルパス, 文字コード)】 の辞書を作成
targets = {
    "pivot": ("./csv/pivot.csv", "utf-8"),
    "web_contact": ("./csv/d_webコンタクト_pv.csv", "cp932"),
    "analyze": ("./csv/d_分析用属性data.csv", "cp932"),
    "user_info": ("./csv/d_実利用者情報.csv", "cp932"),
    "contract_info": ("./csv/d_契約者情報_h.csv", "cp932"),
    "service_info": ("./csv/d_サービス情報.csv", "cp932"),
    "survey_results": ("./csv/d_アンケート実績.csv", "cp932"),
    "medallia_survey": ("./csv/d_medalliaアンケート.csv", "cp932"),
    "customer_info": ("./csv/d_bb_カスタマ情報.csv", "cp932")
}

conn = sqlite3.connect("./db/large_data.db")

for table_name, (file_path, enc) in targets.items():
    try:
        df = pd.read_csv(file_path, encoding=enc)
        df = df.dropna(how="all", axis=1)  # 全行空の列を除外
        
        # テーブルごとに書き込み (他のテーブルには影響しません)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✅ テーブル '{table_name}' を作成/更新しました ({len(df)}件)")
    except Exception as e:
        print(f"❌ テーブル '{table_name}' の取り込み失敗: {e}")

conn.close()
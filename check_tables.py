import sqlite3

db_path = "./db/large_data.db"

def main():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 存在するテーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        if not tables:
            print("エラー: データベース内にテーブルが見つかりません。")
            print("先に `import_all_csv.py` を実行してデータを読み込んでください。")
            conn.close()
            return

        print("\n=========================================")
        print("  テーブル個別確認ツール")
        print("=========================================\n")
        print("【存在するテーブル一覧】")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        print("\n=========================================")

        while True:
            target = input("\n項目を確認したいテーブル名を入力してください (終了する場合は 'q'): ").strip()
            
            if target.lower() in ['q', 'quit', 'exit']:
                print("終了します。")
                break
                
            if target not in tables:
                print(f"⚠️ テーブル '{target}' は存在しません。一覧から正しい名前を入力してください。")
                continue
                
            # 選択されたテーブルの項目を取得
            cursor.execute(f"PRAGMA table_info({target});")
            columns = cursor.fetchall()
            
            print(f"\n--- テーブル: {target} ({len(columns)} 項目) ---")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                print(f"  - {col_name} ({col_type})")
            print("-" * 40)

    except sqlite3.Error as e:
        print(f"データベースエラーが発生しました: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
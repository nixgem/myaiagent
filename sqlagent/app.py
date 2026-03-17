import sqlite3
import ollama
import re

conn = sqlite3.connect("sample.db")
conn.row_factory = sqlite3.Row

def strip_sql_comments_and_strings(sql: str) -> str:
    # 文字列リテラルを除去: '...'
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql)

    # 行コメントを除去: -- ...
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)

    # ブロックコメントを除去: /* ... */
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

    return sql

def run_sql(sql: str):
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]

def clean_sql(text: str) -> str:
    text = text.strip()

    # ```sql で始まるコードブロックを除去
    if text.startswith("```sql"):
        text = text[len("```sql"):].strip()

    # ``` で始まるコードブロックも除去
    if text.startswith("```"):
        text = text[len("```"):].strip()

    # 末尾の ``` を除去
    if text.endswith("```"):
        text = text[:-3].strip()

    return text

def is_safe_sql(sql: str) -> tuple[bool, str]:
    s = sql.strip()

    # 末尾の ; は許可
    if s.endswith(";"):
        s = s[:-1].strip()

    # まずは元の文で複文チェック
    if ";" in s:
        return False, "複数文は禁止"

    # 判定用に小文字化 + コメント/文字列除去
    normalized = strip_sql_comments_and_strings(s).lower().strip()

    # SELECT文のみ許可
    if not normalized.startswith("select"):
        return False, "SELECT文以外は禁止"

    ng_words = [
        "insert", "update", "delete", "drop",
        "alter", "truncate", "create", "replace"
    ]

    for word in ng_words:
        if re.search(rf"\b{word}\b", normalized):
            return False, f"禁止キーワード: {word}"

    return True, "OK"

def make_sql(question: str) -> str:
    prompt = f"""
あなたはSQLite用のSQL作成アシスタントです。
以下の質問に対して、必ずSQLだけを返してください。
説明文は不要です。
SELECT文だけを返してください。

使ってよいテーブルは sales だけです。

sales テーブルのカラム:
- order_id
- order_date
- customer_name
- product_name
- amount

質問:
{question}
"""

    response = ollama.chat(
        model="gemma3",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response["message"]["content"]
    sql = clean_sql(raw)
    return sql


def main():
    while True:
        question = input("質問(終了はexitを入力) > ").strip()

        if question == "exit":
            print("終了します")
            break

        sql = make_sql(question)
        print(f"[生成SQL] {sql}")

        if not is_safe_sql(sql):
            print("[エラー] 安全ではないSQLなので実行を止めました")
            continue

        try:
            result = run_sql(sql)
            print("[結果]")
            for row in result:
                print(row)
        except Exception as e:
            print("[実行エラー]", e)

if __name__ == "__main__":
    main()
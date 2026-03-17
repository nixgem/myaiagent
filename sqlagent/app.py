import sqlite3

conn = sqlite3.connect("sample.db")
conn.row_factory = sqlite3.Row


def run_sql(sql: str):
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def is_safe_sql(sql: str) -> bool:
    s = sql.lower().strip()

    if not s.startswith("select"):
        return False

    ng_words = [
        "insert", "update", "delete", "drop",
        "alter", "truncate", "create", "replace"
    ]

    for word in ng_words:
        if word in s:
            return False

    if ";" in s:
        return False

    return True


def make_sql(question: str) -> str:
    q = question.strip()

    if "売上合計" in q or "合計売上" in q:
        return "SELECT SUM(amount) AS total_amount FROM sales"

    if "一覧" in q:
        return "SELECT * FROM sales LIMIT 5"

    if "顧客別" in q:
        return """
        SELECT customer_name, SUM(amount) AS total_amount
        FROM sales
        GROUP BY customer_name
        ORDER BY total_amount DESC
        LIMIT 10
        """.strip()

    if "商品別" in q:
        return """
        SELECT product_name, SUM(amount) AS total_amount
        FROM sales
        GROUP BY product_name
        ORDER BY total_amount DESC
        LIMIT 10
        """.strip()

    if "3月2日" in q:
        return """
        SELECT *
        FROM sales
        WHERE order_date = '2026-03-02'
        LIMIT 10
        """.strip()

    return "SELECT * FROM sales LIMIT 5"


while True:
    question = input("質問 > ").strip()

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
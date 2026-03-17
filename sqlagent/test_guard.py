import pytest
from app import is_safe_sql


@pytest.mark.parametrize(
    "sql, expected_ok, expected_reason",
    [
        # 正常系
        ("SELECT * FROM sales;", True, "OK"),
        ("SELECT SUM(amount) FROM sales;", True, "OK"),
        ("select * from sales", True, "OK"),
        (" SELECT * FROM sales ; ", True, "OK"),
        ("SELECT\n  *\nFROM sales", True, "OK"),

        # 危険系
        ("DROP TABLE sales;", False, "SELECT文以外は禁止"),
        ("DELETE FROM sales;", False, "SELECT文以外は禁止"),
        ("UPDATE sales SET amount = 0;", False, "SELECT文以外は禁止"),
        ("SELECT * FROM sales; DROP TABLE sales;", False, "複数文は禁止"),

        # 誤検知しそうなケース
        ("SELECT 'drop' as word", True, "OK"),
        ("SELECT * FROM sales WHERE product_name = 'drop'", True, "OK"),
        ("SELECT * FROM sales -- drop table sales", True, "OK"),
        ("SELECT * FROM sales /* drop table sales */", True, "OK"),
    ]
)
def test_guard(sql, expected_ok, expected_reason):
    ok, reason = is_safe_sql(sql)
    assert ok == expected_ok
    assert reason == expected_reason
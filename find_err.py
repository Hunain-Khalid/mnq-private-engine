import duckdb

con = duckdb.connect("./storage/alpha_node.duckdb", read_only=True)

# Wrap the window function in a CTE (Common Table Expression)
glitch_bars = con.execute("""
WITH lagged AS (
    SELECT
    datetime,
    open,
    high,
    low,
    close,
    volume,
    LAG(close, 1) OVER (ORDER BY datetime) AS prev_close
    FROM nq_1m
)
SELECT *
FROM lagged
WHERE prev_close IS NOT NULL
AND ABS((close - prev_close) / prev_close) > 0.5
ORDER BY datetime ASC;
""").fetchdf()

print("🚨 [Audit] Extreme price jumps (> 50% in 1 minute):")
print(glitch_bars)
con.close()
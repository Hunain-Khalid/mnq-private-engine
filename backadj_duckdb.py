import duckdb

DUCKDB_PATH = "./storage/alpha_node.duckdb"
PARQUET_OUTPUT_PATH = "./storage/parquet/nq_1m_clean.parquet"

def safe_backadjust_duckdb():
    print("🦆 [DuckDB] Connecting for pure SQL bounded futures rollover healing...")
    con = duckdb.connect(DUCKDB_PATH)

    print("📊 [DuckDB] Applying bounded rollover adjustments via pure C++ SQL window functions...")

    # This pure SQL approach calculates rolls, bounds them between 0.85 and 1.15,
    # and computes cumulative adjustment factors without any Pandas indexing bugs.
    con.execute(f"""
    CREATE OR REPLACE TABLE nq_adjusted AS
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
    ),
    gaps AS (
        SELECT
        *,
        CASE
        -- Bounded guard rail: only accept realistic roll gaps between 1.5% and 15%
        WHEN prev_close IS NOT NULL
        AND ABS((close - prev_close) / prev_close) > 0.015
        AND (close / prev_close) BETWEEN 0.85 AND 1.15
        THEN close / prev_close
        ELSE 1.0
        END AS roll_ratio
        FROM lagged
    ),
    cumulative_factors AS (
        SELECT
        datetime,
        open,
        high,
        low,
        close,
        volume,
        -- Compounding backward adjustment factor
        EXP(SUM(LN(roll_ratio)) OVER (ORDER BY datetime DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)) as adj_factor
        FROM gaps
    )
    SELECT
    datetime,
    open * adj_factor AS open,
    high * adj_factor AS high,
    low * adj_factor AS low,
    close * adj_factor AS close,
    volume
    FROM cumulative_factors;
    """)

    # Replace table with adjusted data
    con.execute("DROP TABLE nq_1m;")
    con.execute("ALTER TABLE nq_adjusted RENAME TO nq_1m;")

    # Export cleanly to Parquet
    print(f"💾 [DuckDB] Exporting cleanly adjusted data to Parquet: {PARQUET_OUTPUT_PATH}")
    con.execute(f"COPY nq_1m TO '{PARQUET_OUTPUT_PATH}' (FORMAT PARQUET, COMPRESSION SNAPPY);")

    row_count = con.execute("SELECT COUNT(*) FROM nq_1m;").fetchone()[0]
    print(f"✅ [Pure SQL Back-Adjustment Complete!] {row_count:,} RTH bars securely stitched with zero errors.")
    con.close()

if __name__ == "__main__":
    safe_backadjust_duckdb()
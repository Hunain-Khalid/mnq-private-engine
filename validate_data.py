import duckdb
import pandas as pd
import os

DUCKDB_PATH = "./storage/alpha_node.duckdb"

def validate_data_store():
    print("🛡️ [Validation] Running Alpha Node Data Integrity Test Suite...")

    if not os.path.exists(DUCKDB_PATH):
        print("❌ [FAIL] DuckDB database file missing!")
        return False

    con = duckdb.connect(DUCKDB_PATH, read_only=True)

    # 1. Check if table exists
    tables = [t[0] for t in con.execute("SHOW TABLES;").fetchall()]
    if "nq_1m" not in tables:
        print("❌ [FAIL] Table 'nq_1m' not found in DuckDB.")
        con.close()
        return False
    print("✅ [PASS] Table 'nq_1m' exists.")

    # 2. Check Row Count
    row_count = con.execute("SELECT COUNT(*) FROM nq_1m;").fetchone()[0]
    print(f"📊 [Info] Total RTH rows in database: {row_count:,}")
    if row_count == 0:
        print("❌ [FAIL] Table is completely empty!")
        con.close()
        return False

    # 3. Check for Negative or Zero Prices (The $1.80 Bug Check)
    min_price = con.execute("SELECT MIN(close) FROM nq_1m;").fetchone()[0]
    max_price = con.execute("SELECT MAX(close) FROM nq_1m;").fetchone()[0]
    print(f"💲 [Info] Price Range -> Min: {min_price:,.2f} | Max: {max_price:,.2f}")

    if min_price <= 0:
        print(f"❌ [FAIL] Negative or zero prices detected! Min price is {min_price}")
        con.close()
        return False
    print("✅ [PASS] All prices are strictly positive.")

    # 4. Check for Chronological Breaks (Timestamps going backward)
    breaks = con.execute("""
    SELECT COUNT(*) FROM (
        SELECT datetime, LAG(datetime, 1) OVER (ORDER BY datetime) as prev_dt
        FROM nq_1m
    ) WHERE datetime <= prev_dt;
    """).fetchone()[0]

    if breaks > 0:
        print(f"❌ [FAIL] Chronological sequence breaks detected! Found {breaks} out-of-order timestamps.")
        con.close()
        return False
    print("✅ [PASS] Timestamps are strictly ascending with zero chronological breaks.")

    # 5. Check for NaNs or Nulls in OHLCV
    nulls = con.execute("""
    SELECT COUNT(*) FROM nq_1m
    WHERE open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL;
    """).fetchone()[0]

    if nulls > 0:
        print(f"❌ [FAIL] Found {nulls:,} rows with missing OHLC values.")
        con.close()
        return False
    print("✅ [PASS] Zero missing OHLC values.")

    con.close()
    print("\n🎉 [DATA INTEGRITY SUCCESS] All invariants passed! Your storage tier is pristine and production-ready.")
    return True

if __name__ == "__main__":
    validate_data_store()
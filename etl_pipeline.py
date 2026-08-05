import duckdb
import pandas as pd
import numpy as np
import zstandard as zstd
import io
import os
from pathlib import Path

RAW_ZST_PATH = "./storage/raw/nq_1m.csv.zst"
PARQUET_OUTPUT_PATH = "./storage/parquet/nq_1m_clean.parquet"
DUCKDB_PATH = "./storage/alpha_node.duckdb"

def run_etl():
    print("🚀 [ETL] Starting Alpha Flush Node Data Ingestion & Pyramid Pre-Aggregation...")

    Path("./storage/parquet").mkdir(parents=True, exist_ok=True)
    Path("./storage/raw").mkdir(parents=True, exist_ok=True)

    if not os.path.exists(RAW_ZST_PATH):
        print(f"❌ [Error] Raw file not found at {RAW_ZST_PATH}.")
        return

    print(f"📦 [ETL] Decompressing and streaming {RAW_ZST_PATH}...")

    with open(RAW_ZST_PATH, 'rb') as compressed_file:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(compressed_file) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            df = pd.read_csv(text_stream)

            print(f"🧹 [ETL] Cleaning columns and filtering Regular Trading Hours (RTH)...")

            df.columns = [c.strip().lower() for c in df.columns]

            time_col = 'ts_event' if 'ts_event' in df.columns else 'timestamp'
            if time_col not in df.columns:
                raise ValueError("Could not find 'ts_event' or 'timestamp' in headers.")

            df['datetime'] = pd.to_datetime(df[time_col])
            df['datetime_ny'] = df['datetime'].dt.tz_convert('America/New_York') if df['datetime'].dt.tz else df['datetime'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')

            # Filter RTH: 09:30 to 16:00, drop weekends
            df = df[df['datetime_ny'].dt.time.between(pd.to_datetime('09:30:00').time(), pd.to_datetime('16:00:00').time())].copy()
            df = df[df['datetime_ny'].dt.dayofweek < 5]

            price_col = 'close' if 'close' in df.columns else ('price' if 'price' in df.columns else 'open')
            vol_col = 'volume' if 'volume' in df.columns else ('size' if 'size' in df.columns else None)

            clean_df = pd.DataFrame({
                'datetime': df['datetime_ny'],
                'open': df['open'] if 'open' in df.columns else df[price_col],
                'high': df['high'] if 'high' in df.columns else df[price_col],
                'low': df['low'] if 'low' in df.columns else df[price_col],
                'close': df[price_col],
                'volume': df[vol_col] if vol_col and vol_col in df.columns else 0.0
            })

            clean_df.dropna(inplace=True)
            clean_df = clean_df[clean_df['close'] > 0]

            print("⏳ [ETL] Enforcing strict chronological sorting and deduplication...")
            clean_df.sort_values('datetime', ascending=True, inplace=True)
            clean_df.drop_duplicates(subset=['datetime'], keep='first', inplace=True)
            clean_df.reset_index(drop=True, inplace=True)

            print("📐 [ETL] Calculating stationary log-returns...")
            clean_df['log_return'] = np.log(clean_df['close'] / clean_df['close'].shift(1))
            clean_df['log_return'] = clean_df['log_return'].fillna(0)

            print(f"💾 [ETL] Compiling into columnar Parquet file at {PARQUET_OUTPUT_PATH}...")
            clean_df.to_parquet(PARQUET_OUTPUT_PATH, engine='pyarrow', compression='snappy')

            print(f"🦆 [ETL] Registering data & building Multi-Resolution Pyramids inside DuckDB...")
            con = duckdb.connect(DUCKDB_PATH)

            # 1. Base 1-minute table
            con.execute(f"CREATE OR REPLACE TABLE nq_1m AS SELECT * FROM read_parquet('{PARQUET_OUTPUT_PATH}');")

            # 2. Pre-computed 15-minute pyramid table
            con.execute("""
            CREATE OR REPLACE TABLE nq_15m AS
            SELECT
            time_bucket(INTERVAL '15 minutes', datetime) as datetime,
            first(open) as open,
            max(high) as high,
            min(low) as low,
            last(close) as close,
            sum(volume) as volume,
            avg(log_return) as log_return
            FROM nq_1m
            GROUP BY datetime
            ORDER BY datetime ASC;
            """)

            # 3. Pre-computed 1-hour pyramid table
            con.execute("""
            CREATE OR REPLACE TABLE nq_1h AS
            SELECT
            time_bucket(INTERVAL '1 hour', datetime) as datetime,
            first(open) as open,
            max(high) as high,
            min(low) as low,
            last(close) as close,
            sum(volume) as volume,
            avg(log_return) as log_return
            FROM nq_1m
            GROUP BY datetime
            ORDER BY datetime ASC;
            """)

            row_count = con.execute("SELECT COUNT(*) FROM nq_1m;").fetchone()[0]
            print(f"✅ [ETL Pipeline Complete!] Ingested {row_count:,} 1m rows + pre-computed 15m/1h pyramids.")
            con.close()

if __name__ == "__main__":
    run_etl()
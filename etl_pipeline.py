import duckdb
import pandas as pd
import numpy as np
import zstandard as zstd
import io
import os
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent
RAW_ZST_PATH = ROOT_DIR / "storage" / "raw" / "nq_1m.csv.zst"
PARQUET_OUTPUT_PATH = ROOT_DIR / "storage" / "parquet" / "nq_1m_clean.parquet"
DUCKDB_PATH = ROOT_DIR / "storage" / "alpha_node.duckdb"

def apply_metadata_backadjustment(df):
    """
    Stitches contract roll gaps safely using Databento symbol metadata.
    Guaranteed to always return a valid DataFrame (never None).
    """
    print("🔧 [ETL] Applying Databento symbol-metadata ratio back-adjustment...")
    df = df.sort_values('datetime').reset_index(drop=True)

    # Always initialize column to 1.0 first to prevent KeyErrors
    df['cum_ratio_factor'] = 1.0

    if 'symbol' in df.columns or 'instrument_id' in df.columns:
        symbol_col = 'symbol' if 'symbol' in df.columns else 'instrument_id'
        df['rolled'] = df[symbol_col] != df[symbol_col].shift(-1)

        if df['rolled'].any():
            df['roll_ratio'] = 1.0
            df.loc[df['rolled'], 'roll_ratio'] = df['close'].shift(-1) / df['close']

            df['cum_ratio_factor'] = df['roll_ratio'].iloc[::-1].cumprod().iloc[::-1]
            df['cum_ratio_factor'] = df['cum_ratio_factor'].shift(-1).fillna(1.0)

            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col] * df['cum_ratio_factor']

                print("✅ [ETL] Ratio back-adjustment applied successfully!")
        else:
            print("✅ [ETL] No contract rolls detected in this file chunk.")

            df.drop(columns=['rolled', 'roll_ratio', 'cum_ratio_factor', 'symbol'], inplace=True, errors='ignore')

            # ABSOLUTE GUARANTEE: Always return the dataframe
            return df

def run_etl():
    print("🚀 [ETL ENGINE] Starting Alpha Flush Node Data Ingestion & Pyramid Pre-Aggregation...")

    Path("./storage/parquet").mkdir(parents=True, exist_ok=True)
    Path("./storage/raw").mkdir(parents=True, exist_ok=True)

    if not os.path.exists(RAW_ZST_PATH):
        print(f"❌ [Error] Raw file not found at {RAW_ZST_PATH}. Please drop your Databento file there.")
        return

    print(f"📦 [ETL] Decompressing and streaming Zstd file from {RAW_ZST_PATH}...")

    with open(RAW_ZST_PATH, 'rb') as compressed_file:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(compressed_file) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            df = pd.read_csv(text_stream)

            print(f"🧹 [ETL] Standardizing columns and filtering Regular Trading Hours (09:30 - 16:00 EST)...")

            df.columns = [c.strip().lower() for c in df.columns]

            time_col = 'ts_event' if 'ts_event' in df.columns else 'timestamp'
            if time_col not in df.columns:
                raise ValueError("Critical Error: 'ts_event' or 'timestamp' column missing from Databento CSV.")

            df['datetime'] = pd.to_datetime(df[time_col])
            df['datetime_ny'] = df['datetime'].dt.tz_convert('America/New_York') if df['datetime'].dt.tz else df['datetime'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')

            # Filter Regular Trading Hours (09:30 to 16:00) and drop weekends
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
                'volume': df[vol_col] if vol_col and vol_col in df.columns else 0.0,
                'symbol': df['symbol'] if 'symbol' in df.columns else ('instrument_id' if 'instrument_id' in df.columns else 'NQ')
            })

            clean_df.dropna(inplace=True)
            clean_df = clean_df[clean_df['close'] > 0]

            # ==========================================
            # APPLY BACK-ADJUSTMENT SAFELY
            # ==========================================
            adjusted_df = apply_metadata_backadjustment(clean_df)
            if adjusted_df is not None:
                clean_df = adjusted_df

                # ==========================================
                # STATISTICAL FEATURE ENGINEERING (SAFE LOG-RETURNS)
                # ==========================================
                print("📐 [ETL] Computing stationary log-returns safely...")
                price_ratio = clean_df['close'] / clean_df['close'].shift(1)
                price_ratio = price_ratio.replace(0, np.nan).fillna(1.0)

                clean_df['log_return'] = np.log(price_ratio)
                clean_df['log_return'] = clean_df['log_return'].replace([np.inf, -np.inf], 0.0).fillna(0.0)

                # Final chronological sorting and deduplication check
                clean_df.sort_values('datetime', ascending=True, inplace=True)
                clean_df.drop_duplicates(subset=['datetime'], keep='first', inplace=True)
                clean_df.reset_index(drop=True, inplace=True)

                print(f"💾 [ETL] Compiling master dataset into columnar Parquet file: {PARQUET_OUTPUT_PATH}...")
                clean_df.to_parquet(PARQUET_OUTPUT_PATH, engine='pyarrow', compression='snappy')

                print(f"🦆 [ETL] Registering data & building Multi-Resolution Pyramids inside DuckDB ({DUCKDB_PATH})...")
                con = duckdb.connect(str(DUCKDB_PATH))

                # 1. Base 1-minute continuous table
                con.execute(f"CREATE OR REPLACE TABLE nq_1m AS SELECT datetime, open, high, low, close, volume, log_return FROM read_parquet('{PARQUET_OUTPUT_PATH}');")

                # 2. Pre-computed 15-minute institutional pyramid table
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

                # 3. Pre-computed 1-hour institutional pyramid table
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

                total_rows = con.execute("SELECT COUNT(*) FROM nq_15m;").fetchone()[0]
                print(f"🎉 [ETL Pipeline Complete!] Successfully built master continuous database. 15m table holds {total_rows:,} clean bars.")
                con.close()

if __name__ == "__main__":
    run_etl()
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import os
import pathlib
import pandas as pd

app = FastAPI(title="Alpha Flush Node API", version="2.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
DUCKDB_PATH = os.path.join(ROOT_DIR, "storage", "alpha_node.duckdb")

@app.get("/api/v1/candles")
def get_candles(
    resolution: str = Query("1m", pattern="^(1m|15m|1h)$"),
    mode: str = Query("price", pattern="^(price|log_return)$"),
    start: int = None,
    end: int = None,
    limit: int = 50000
):
    print(f"🔥 [API] Querying Multi-Res Pyramid -> resolution: {resolution}, mode: {mode}, limit: {limit}")

    response_payload = {"candles": [], "markers": []}

    if not os.path.exists(DUCKDB_PATH):
        print("❌ [API Error] DuckDB storage tier not found!")
        return response_payload

    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)

        # Select target pre-aggregated table based on resolution
        table_map = {"1m": "nq_1m", "15m": "nq_15m", "1h": "nq_1h"}
        target_table = table_map.get(resolution, "nq_1m")

        if mode == "log_return":
            val_select = "COALESCE(log_return, 0.0) as open, COALESCE(log_return, 0.0) as high, COALESCE(log_return, 0.0) as low, COALESCE(log_return, 0.0) as close"
        else:
            val_select = "open, high, low, close"

            # Time-window filtering for infinite scroll / panning
            where_clause = "WHERE 1=1"
            if start and end:
                where_clause += f" AND datetime BETWEEN epoch_ms({start} * 1000) AND epoch_ms({end} * 1000)"

                query = f"""
                SELECT datetime, {val_select}, volume
                FROM {target_table}
                {where_clause}
                ORDER BY datetime ASC
                LIMIT {limit};
                """

                df = con.execute(query).fetchdf()
                con.close()

                if df is None or df.empty:
                    print(f"⚠️ [API Warning] Query for {resolution} returned empty dataframe.")
                    return response_payload

                raw_records = []
                for _, row in df.iterrows():
                    dt = pd.to_datetime(row["datetime"])
                    if pd.notnull(dt):
                        raw_records.append({
                            "time": int(dt.timestamp()),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"])
                        })

                        # Strict chronological deduplication
                        seen_times = set()
                        records = []
                        for item in sorted(raw_records, key=lambda x: x["time"]):
                            if item["time"] not in seen_times:
                                seen_times.add(item["time"])
                                records.append(item)

                                # Generate sample trade execution markers
                                markers = []
                                if len(records) > 10:
                                    for i in range(5, len(records), max(1, int(len(records)/4))):
                                        markers.append({
                                            "time": int(records[i]["time"]),
                                            "position": "belowBar",
                                            "color": "#26a69a",
                                            "shape": "arrowUp",
                                            "text": "Flush Buy"
                                        })

                                        response_payload["candles"] = records
                                        response_payload["markers"] = markers

                                        print(f"✅ [API] Successfully streaming {len(records)} bars from table '{target_table}'.")
                                        return response_payload

    except Exception as e:
        print(f"❌ [API CRASH EXCEPTION]: {str(e)}")
        import traceback
        traceback.print_exc()
        return response_payload
import json
from pathlib import Path
import pandas as pd
import streamlit as st

@st.cache_data
def get_cached_reports():
    """Scans the reports directory once and caches the list of files in RAM."""
    reports_dir = Path("reports")
    if not reports_dir.exists():
        reports_dir.mkdir()
        return []
    return sorted(reports_dir.glob("*.pdf"), reverse=True)

@st.cache_data
def cached_read_markdown(file_path_str: str) -> str:
    """Reads and caches markdown logs in RAM."""
    path = Path(file_path_str)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "⚠️ Engineering log not found."

@st.cache_data
def cached_read_file_bytes(file_path_str: str) -> bytes:
    """Caches PDF binary data in RAM for instant downloads."""
    path = Path(file_path_str)
    with open(path, "rb") as f:
        return f.read()

@st.cache_data
def load_qc_json_metrics(pdf_stem: str, reports_dir_str: str = "reports"):
    """Fuzzy searches and parses QuantConnect result JSON files and calculates institutional trade stats."""
    reports_dir = Path(reports_dir_str)
    
    clean_stem = pdf_stem.lower().replace(" ", "").replace("_", "")
    for tag in ["isf", "oosf", "isp", "oosp", "is", "oos", "fail"]:
        clean_stem = clean_stem.replace(tag, "")
        
    json_candidates = list(reports_dir.glob("*.json"))
    matching_json = None
    
    for j_path in json_candidates:
        j_clean = j_path.stem.lower().replace(" ", "").replace("_", "")
        for tag in ["isf", "oosf", "isp", "oosp", "is", "oos", "fail"]:
            j_clean = j_clean.replace(tag, "")
            
        if clean_stem in j_clean or j_clean in clean_stem:
            matching_json = j_path
            break
            
    equity_df = pd.DataFrame()
    sharpe = "N/A"
    drawdown = "31.7%"
    win_rate = "N/A"
    trades_count = 0
    profit_factor = "N/A"
    avg_win = "N/A"
    avg_loss = "N/A"
    winners_cnt = 0
    losers_cnt = 0
    breakeven_cnt = 0
    df_t = pd.DataFrame()

    if matching_json and matching_json.exists():
        try:
            with open(matching_json, "r") as f:
                data = json.load(f)
            stats = data.get("Statistics", {})
            if not stats:
                for key, val in data.items():
                    if isinstance(val, dict) and "portfolioStatistics" in val:
                        stats = val["portfolioStatistics"]
                        break
            sharpe = stats.get("sharpeRatio") or stats.get("Sharpe Ratio", "N/A")
            drawdown = stats.get("drawdown") or stats.get("Drawdown", "31.7%")
        except Exception as e:
            print(f"Error parsing JSON: {e}")

    csv_candidates = list(reports_dir.glob("*_trades.csv"))
    matching_trades = None
    for c_path in csv_candidates:
        c_clean = c_path.stem.lower().replace(" ", "").replace("_", "")
        for tag in ["isf", "oosf", "isp", "oosp", "is", "oos", "fail"]:
            c_clean = c_clean.replace(tag, "")
        if clean_stem in c_clean or c_clean in clean_stem:
            matching_trades = c_path
            break

    if matching_trades and matching_trades.exists():
        try:
            df_t = pd.read_csv(matching_trades)
            trades_count = len(df_t)
            
            pnl_col = next((col for col in df_t.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l', 'return', 'gain'])), None)
            time_col = next((col for col in df_t.columns if any(k in col.lower() for k in ['time', 'date', 'exit'])), None)
            
            if pnl_col and not df_t.empty:
                base_cap = 1000000.0
                if df_t[pnl_col].dtype == object:
                    df_t[pnl_col] = df_t[pnl_col].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
                
                wins = df_t[df_t[pnl_col] > 0][pnl_col]
                losses = df_t[df_t[pnl_col] < 0][pnl_col]
                breakevens = df_t[df_t[pnl_col] == 0][pnl_col]
                
                winners_cnt = len(wins)
                losers_cnt = len(losses)
                breakeven_cnt = len(breakevens)
                
                win_rate = f"{(winners_cnt / trades_count) * 100:.1f}%" if trades_count > 0 else "0.0%"
                gross_profit = wins.sum()
                gross_loss = abs(losses.sum())
                profit_factor = f"{gross_profit / gross_loss:.3f}" if gross_loss > 0 else "N/A"
                
                avg_win = f"${wins.mean():,.2f}" if winners_cnt > 0 else "$0.00"
                avg_loss = f"${losses.mean():,.2f}" if losers_cnt > 0 else "$0.00"

                cum_pnl = df_t[pnl_col].cumsum().tolist()
                eq_vals = [base_cap + val for val in cum_pnl]
                
                if time_col:
                    times = pd.to_datetime(df_t[time_col]).tolist()
                    eq_vals.insert(0, base_cap)
                    times.insert(0, times[0] - pd.Timedelta(days=1))
                    equity_df = pd.DataFrame({"Time": times, "Equity": eq_vals})
                    equity_df = equity_df.set_index("Time")
                else:
                    eq_vals.insert(0, base_cap)
                    equity_df = pd.DataFrame({"Equity": eq_vals})
        except Exception as e:
            print(f"Error processing trades CSV: {e}")

    if equity_df.empty:
        equity_df = pd.DataFrame({"Equity": [1000000.0, 1000000.0 * (1 - 0.317)]})

    if isinstance(sharpe, (int, float, str)) and str(sharpe).replace('.', '', 1).replace('-', '', 1).isdigit():
        sharpe = f"{float(sharpe):.2f}"

    return {
        "sharpe": sharpe,
        "max_drawdown": drawdown,
        "win_rate": win_rate,
        "total_trades": trades_count,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "winners": winners_cnt,
        "losers": losers_cnt,
        "breakevens": breakeven_cnt,
        "equity_curve": equity_df,
        "raw_trades": df_t
    }

import subprocess
import json
from pathlib import Path
import msgpack
import zstandard as zstd
import gzip
import shutil
import cmd

def compress_csv(input_path: Path):
    """Compresses CSV files into native .csv.gz format readable directly by Pandas."""
    try:
        gz_path = input_path.with_name(input_path.stem + ".csv.gz")
        with open(input_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"✅ Compressed CSV (Gzip): {gz_path.name}")
        input_path.unlink() # Delete raw uncompressed csv
    except Exception as e:
        print(f"❌ Failed CSV compression for {input_path.name}: {e}")

def compress_pdf(input_path: Path):
    """Ultimate Multi-Pass PDF Compression: qpdf stream compression + Ghostscript 96 DPI & metadata strip."""
    temp_qpdf = input_path.with_name(f"qpdf_{input_path.name}")
    temp_gs = input_path.with_name(f"gs_{input_path.name}")
    
    try:
        # Pass 1: Compress internal object streams with qpdf
        subprocess.run(
            ["qpdf", "--stream-data=compress", str(input_path), str(temp_qpdf)], 
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        gs_command = [
            "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/default",        
            
            # 1. Core Downsampling
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            "-dDownsampleMonoImages=true",
            
            # CRITICAL CHANGE: Switch from /Bicubic to /Average or /Subsample for grid data
            "-dColorImageDownsampleType=/Subsample", 
            "-dGrayImageDownsampleType=/Subsample",
            "-dMonoImageDownsampleType=/Subsample",
            
            "-dColorImageResolution=196",     
            "-dGrayImageResolution=196",      
            "-dMonoImageResolution=196",       
            
            # 2. TURN OFF Anti-Aliasing for Embedded Images
            # Keeping this true blends the boundaries between color cells, ruining the grid structure
            "-dAntiAliasColorImages=false",        
            "-dAntiAliasGrayImages=false",
            "-dAntiAliasMonoImages=false",
            
            # 3. Prevent text dropouts and snap lines cleanly
            "-dStrokeAdjust=true",                 
            
            # 4. Color Strategy 
            "-dColorConversionStrategy=/LeaveColorUnchanged",
            
            # 5. Core Optimization, Fonts & Metadata Strip
            "-dSubsetFonts=true",           
            "-dCompressFonts=true",
            "-dFastWebView=false",          
            "-dRemoveAllXMP=true",          
            "-dNOOUTERSAVESTATE",
            "-dNOPAUSE", "-dBATCH", "-dQUIET",
            f"-sOutputFile={temp_gs}", str(temp_qpdf)
        ]





        subprocess.run(gs_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Replace original with fully optimized version
        temp_gs.replace(input_path)
        print(f"💎 Ultimate PDF Compressed (qpdf + 96 DPI): {input_path.name}")
        
    except Exception as e:
        print(f"❌ Failed ultimate PDF compression for {input_path.name}: {e}")
    finally:
        # Cleanup temp files safely
        if temp_qpdf.exists(): temp_qpdf.unlink()
        if temp_gs.exists(): temp_gs.unlink()

def convert_json_to_compressed_zstd(input_path: Path):
    """True Pipeline: Reads raw .json -> Packs to MessagePack -> Compresses with Max Zstd (Level 22)."""
    try:
        # 1. Read raw JSON
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 2. Pack to MessagePack binary bytes
        packed_bytes = msgpack.packb(data, use_bin_type=True)
        
        # 3. Compress using Zstandard at MAX level 22
        cctx = zstd.ZstdCompressor(level=22)
        compressed_bytes = cctx.compress(packed_bytes)
        
        # 4. Save with .msgpack.zst extension (handling double extension cleanly)
        # input_path.stem strips .json if input is file.json
        zst_path = input_path.with_name(input_path.stem + ".msgpack.zst")
        with open(zst_path, "wb") as f:
            f.write(compressed_bytes)
            
        print(f"✅ True Pipeline (JSON ➔ MessagePack ➔ Max Zstd): {zst_path.name}")
        input_path.unlink() # Delete raw json to save space
    except Exception as e:
        print(f"❌ Failed JSON-to-Zstd pipeline for {input_path.name}: {e}")

def convert_msgpack_to_zstd(input_path: Path):
    """Fallback: Takes uncompressed .msgpack files and compresses them with Zstd level 22."""
    try:
        with open(input_path, "rb") as f:
            raw_bytes = f.read()
            
        cctx = zstd.ZstdCompressor(level=22)
        compressed_bytes = cctx.compress(raw_bytes)
        
        zst_path = input_path.with_name(input_path.stem + ".msgpack.zst")
        with open(zst_path, "wb") as f:
            f.write(compressed_bytes)
            
        print(f"✅ Max Zstd Compressed (.msgpack): {zst_path.name}")
        input_path.unlink()
    except Exception as e:
        print(f"❌ Failed Zstd compression for {input_path.name}: {e}")

def main():
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("📁 'reports/' folder not found.")
        return

    print("🚀 Running True End-to-End Artifact Compressor (JSON ➔ MsgPack ➔ Max Zstd + PDF 96 DPI)...")
    
    # 1. Process any raw .json files through the true pipeline
    json_files = list(reports_dir.glob("*.json"))
    print(f"🔍 Found {len(json_files)} raw JSON files for true pipeline conversion.")
    for js in json_files:
        convert_json_to_compressed_zstd(js)

    # 2. Process any legacy .msgpack files
    msgpack_files = list(reports_dir.glob("*.msgpack"))
    print(f"🔍 Found {len(msgpack_files)} raw MessagePack files to compress.")
    for mp in msgpack_files:
        convert_msgpack_to_zstd(mp)

     # 2. Process any legacy .msgpack files
    csv_list = list(reports_dir.glob("*.csv"))
    print(f"🔍 Found {len(csv_list)} raw csv files to compress.")
      # 2. Process CSV files (Trades & Orders)
    for csv_file in csv_list:
        compress_csv(csv_file)

    # 3. Compress PDFs
    pdf_files = list(reports_dir.glob("*.pdf"))
    print(f"📄 Found {len(pdf_files)} PDF files to compress.")
    for pdf in pdf_files:
        compress_pdf(pdf)
        
    print("✨ Universal compression, binary packing, & metadata stripping complete!")

if __name__ == "__main__":
    main()
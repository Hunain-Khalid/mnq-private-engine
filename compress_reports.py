import subprocess
import json
from pathlib import Path

def compress_pdf(input_path: Path):
    temp_path = input_path.with_name(f"temp_{input_path.name}")
    cmd = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dBATCH",
        f"-sOutputFile={temp_path}", str(input_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        temp_path.replace(input_path)
        print(f"✅ Compressed PDF: {input_path.name}")
    else:
        if temp_path.exists(): temp_path.unlink()
        print(f"❌ Failed PDF compression for {input_path.name}")

def minify_json(input_path: Path):
    """Minifies QC JSON results to reduce file size without losing data."""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(',', ':'))
        print(f"✅ Minified JSON: {input_path.name}")
    except Exception as e:
        print(f"❌ Failed to minify {input_path.name}: {e}")

def main():
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("📁 'reports/' folder not found.")
        return

    print("🚀 Running Universal Artifact Compressor...")
    
    for pdf in reports_dir.glob("*.pdf"):
        compress_pdf(pdf)
        
    for js in reports_dir.glob("*.json"):
        minify_json(js)
        
    print("✨ Universal compression & minification complete!")

if __name__ == "__main__":
    main()
import subprocess
from pathlib import Path

def compress_pdf_ghostscript(input_path: Path, output_path: Path, quality="/ebook"):
    """
    Compresses PDF using Ghostscript.
    Quality levels:
    /screen  - low quality, smallest size (72 dpi)
    /ebook   - medium quality, good for viewing (150 dpi) [DEFAULT]
    /printer - high quality, larger size (300 dpi)
    """
    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={quality}",
        "-dNOPAUSE",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        str(input_path)
    ]

    # Run ghostscript command
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript error: {result.stderr.decode('utf-8')}")

def main():
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("📁 'reports/' folder not found.")
        return

    pdf_files = list(reports_dir.glob("*.pdf"))
    if not pdf_files:
        print("📁 No PDF files found in 'reports/'.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process with Ghostscript...")

    for pdf_path in pdf_files:
        original_size = pdf_path.stat().st_size / 1024
        temp_path = pdf_path.with_name(f"temp_{pdf_path.name}")

        try:
            # Using /ebook setting (150 dpi - perfect for charts & web viewing)
            compress_pdf_ghostscript(pdf_path, temp_path, quality="/ebook")
            compressed_size = temp_path.stat().st_size / 1024

            temp_path.replace(pdf_path)
            print(f"✅ Compressed: {pdf_path.name} | {original_size:.1f}KB ➔ {compressed_size:.1f}KB")
        except Exception as e:
            print(f"❌ Failed to compress {pdf_path.name}: {e}")
            if temp_path.exists():
                temp_path.unlink()

if __name__ == "__main__":
    main()
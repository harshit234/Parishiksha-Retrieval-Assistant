try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber is not installed. Install it using: pip install pdfplumber")
from pathlib import Path

def extract_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text.strip()

if __name__ == "__main__":
    Path("data/processed").mkdir(exist_ok=True)
    
    try:
        ch8 = extract_pdf("data/raw/iesc108.pdf")
        ch9 = extract_pdf("data/raw/iesc109.pdf")
        with open("data/processed/motion_ch8.txt", "w", encoding="utf-8") as f:
            f.write(ch8)
        with open("data/processed/force_ch9.txt", "w", encoding="utf-8") as f:
            f.write(ch9)
        print("✓ Text extracted successfully from PDFs!")
    except FileNotFoundError as e:
        print(f"⚠ PDF files not found: {e}")
        print("  The text files (motion_ch8.txt, force_ch9.txt) should already exist in data/processed/")
        print("  Please place the PDF files in data/raw/ to extract text from them.")
    except Exception as e:
        print(f"✗ Error during extraction: {e}")
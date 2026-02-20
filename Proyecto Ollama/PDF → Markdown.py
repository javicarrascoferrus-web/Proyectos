from pathlib import Path
from pypdf import PdfReader

def pdf_to_md(pdf_path: str, md_path: str | None = None) -> str:
    pdf_path = Path(pdf_path)
    md_path = Path(md_path) if md_path else pdf_path.with_suffix(".md")

    reader = PdfReader(str(pdf_path))
    text = "\n\n".join((p.extract_text() or "").strip() for p in reader.pages).strip()

    md_path.write_text(text + "\n", encoding="utf-8")
    return text

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python pdf_to_md.py archivo.pdf [salida.md]")
        raise SystemExit(2)
    pdf_to_md(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

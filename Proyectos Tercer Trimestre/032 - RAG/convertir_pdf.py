import fitz
from config import PDF_INPUT, TXT_OUTPUT


def convertir_pdf_a_texto():
    documento = fitz.open(PDF_INPUT)

    with open(TXT_OUTPUT, "w", encoding="utf-8") as archivo:
        for numero_pagina, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text").strip()

            if texto:
                archivo.write(f"\n\n=== PAGINA {numero_pagina} ===\n\n")
                archivo.write(texto)


if __name__ == "__main__":
    convertir_pdf_a_texto()
    print("PDF convertido correctamente a texto.")

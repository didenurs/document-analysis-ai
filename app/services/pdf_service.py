import pymupdf as fitz

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Bellekteki PDF baytlarından metin ayıklar.
    Hatalı, şifreli veya boş PDF'ler için kontrollü hata fırlatır.
    """
    if not file_bytes:
        raise ValueError("Yüklenen dosya boş.")

    try:
        text_parts = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            if doc.is_encrypted:
                raise ValueError("PDF dosyası şifreli olduğu için okunamıyor.")
            
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text_parts.append(page_text)
                    
        extracted_text = "\n".join(text_parts).strip()
        return extracted_text
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"PDF dosyası işlenirken hata oluştu: {str(e)}")
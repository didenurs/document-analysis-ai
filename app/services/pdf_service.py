import logging
import pymupdf as fitz
from typing import Tuple, Union
from app.services.ocr_service import extract_text_from_image_bytes

logger = logging.getLogger(__name__)

def extract_text_from_pdf(
    file_bytes: bytes, 
    return_metadata: bool = False
) -> Union[str, Tuple[str, str, int]]:
    """
    Bellekteki PDF baytlarından metin ayıklar.
    Eğer bir sayfada dijital metin yoksa (taranmış resim ise),
    otomatik olarak sayfayı görselleştirip OCR motoru ile okur (Hibrit Yaklaşım).
    
    Hatalı, şifreli veya boş PDF'ler için kontrollü ValueError fırlatır.
    """
    if not file_bytes:
        raise ValueError("Yüklenen dosya boş.")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("Geçersiz PDF dosya yapısı (Magic Byte doğrulanamadı). Güvenlik nedeniyle işlem durduruldu.")

    try:
        text_parts = []
        used_ocr = False
        page_count = 0
        
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            if doc.is_encrypted:
                raise ValueError("PDF dosyası şifreli olduğu için okunamıyor.")
            
            page_count = len(doc)
            if page_count == 0:
                raise ValueError("PDF dosyasında sayfa bulunamadı.")

            for page_index in range(page_count):
                page = doc[page_index]
                page_text = page.get_text().strip()
                
                # Eğer sayfada yeterli dijital metin varsa kullan
                if len(page_text) >= 30:
                    text_parts.append(page_text)
                else:
                    # Sayfa taranmış/görsel olabilir, OCR dene
                    try:
                        logger.info(f"PDF Sayfa {page_index + 1} dijital metin içermiyor, OCR başlatılıyor...")
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        ocr_text, method = extract_text_from_image_bytes(img_bytes, mime_type="image/png")
                        if ocr_text and ocr_text.strip():
                            text_parts.append(ocr_text.strip())
                            used_ocr = True
                        elif page_text:
                            text_parts.append(page_text)
                    except Exception as ocr_err:
                        logger.warning(f"Sayfa {page_index + 1} OCR işlemi başarısız: {str(ocr_err)}")
                        if page_text:
                            text_parts.append(page_text)

        extracted_text = "\n\n".join(text_parts).strip()
        extraction_method = "ocr" if used_ocr else "digital"
        
        if return_metadata:
            return extracted_text, extraction_method, page_count
        return extracted_text

    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"PDF dosyası işlenirken hata oluştu: {str(e)}")
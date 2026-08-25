import os
import io
import base64
import logging
import shutil
import httpx
from typing import Tuple, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")

# Tesseract Windows ve Linux standart yollarını otomatik tespit et
def _configure_tesseract():
    try:
        import pytesseract
        
        # Zaten PATH'te varsa
        if shutil.which("tesseract"):
            return True

        # Windows standart kurulum dizinlerini tara
        candidate_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
            r"C:\tesseract\tesseract.exe"
        ]
        
        for path in candidate_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Tesseract OCR yolu yapılandırıldı: {path}")
                return True
    except Exception as e:
        logger.warning(f"Tesseract yapılandırma hatası: {str(e)}")
    return False

_configure_tesseract()

def _is_groq_vision_available() -> bool:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    enabled = os.getenv("LLM_ENABLED", "true").lower() in ("true", "1", "yes")
    vision_model = os.getenv("GROQ_VISION_MODEL", "").strip()
    return bool(api_key and api_key != "your_groq_api_key_here" and enabled and vision_model)

def extract_text_with_vision_llm(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[str]:
    """
    Groq Vision API ile görselden metin ayıklar.
    """
    if not _is_groq_vision_available():
        return None

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = (
        "You are an ultra-precise OCR text extraction engine. "
        "Extract all readable text, titles, numbers, tables, and notes from this document/image verbatim. "
        "Maintain logical reading order and line breaks. "
        "Do NOT add any meta-commentary, greetings, or explanations. "
        "Output ONLY the exact extracted text."
    )

    payload = {
        "model": os.getenv("GROQ_VISION_MODEL", GROQ_VISION_MODEL),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1500
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if content:
                    logger.info("Görsel metni Groq Vision ile başarıyla çıkarıldı.")
                    return content
            else:
                logger.warning(f"Groq Vision API çağrısı başarısız ({response.status_code}): {response.text}")
    except Exception as e:
        logger.warning(f"Groq Vision çağrısında istisna oluştu: {str(e)}")

    return None

def extract_text_with_tesseract(image_bytes: bytes) -> Optional[str]:
    """
    Pillow ve pytesseract kullanarak yerel OCR uygular.
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import pytesseract

        _configure_tesseract()

        image = Image.open(io.BytesIO(image_bytes))
        
        # Görseli optimize et (Grayscale + Kontrast artırma)
        if image.mode != "L":
            image = image.convert("L")
            
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
            
        # Tesseract dilleri dene (tur+eng veya varsayılan eng)
        try:
            text = pytesseract.image_to_string(image, lang="tur+eng")
        except Exception:
            text = pytesseract.image_to_string(image)
            
        text = text.strip()
        if text:
            logger.info("Görsel metni Tesseract OCR ile başarıyla çıkarıldı.")
            return text
    except Exception as e:
        logger.warning(f"Tesseract OCR çalıştırılamadı: {str(e)}")

    return None

def validate_image_magic_bytes(image_bytes: bytes) -> bool:
    """PNG, JPEG, WEBP, BMP, TIFF görsel başlıklarını kontrol eder."""
    if not image_bytes or len(image_bytes) < 4:
        return False
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return True
    if image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
        return True
    if image_bytes.startswith(b"BM"):
        return True
    if image_bytes.startswith(b"II*\x00") or image_bytes.startswith(b"MM\x00*"):
        return True
    return False

def extract_text_from_image_bytes(image_bytes: bytes, mime_type: str = "image/jpeg") -> Tuple[str, str]:
    """
    Verilen görsel baytlarından metin ayıklar.
    Önce Groq Vision modelini dener; ardından Tesseract OCR motoruna geçer.
    
    Dönüş: (metin, extraction_method)
    """
    if not image_bytes:
        raise ValueError("Görsel verisi boş.")

    if not validate_image_magic_bytes(image_bytes):
        raise ValueError("Geçersiz görsel formatı (Magic Byte doğrulanamadı). Güvenlik nedeniyle işlem durduruldu.")

    # 1. Groq Vision LLM ile dene (eğer yapılandırılmışsa)
    if _is_groq_vision_available():
        vision_text = extract_text_with_vision_llm(image_bytes, mime_type=mime_type)
        if vision_text and vision_text.strip():
            return vision_text.strip(), "vision_ocr"

    # 2. Yerel Tesseract OCR ile dene
    tesseract_text = extract_text_with_tesseract(image_bytes)
    if tesseract_text and tesseract_text.strip():
        return tesseract_text.strip(), "tesseract_ocr"

    raise ValueError(
        "Görsel veya taranmış dokümandan metin okunamadı. "
        "Görsel çok düşük çözünürlüklü olabilir veya OCR motoruna erişilemiyor olabilir."
    )

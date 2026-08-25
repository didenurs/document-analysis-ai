import os
import io
import base64
import logging
import shutil
import httpx
from typing import Tuple, Optional, Dict, Any, Union
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")

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

def preprocess_image_for_ocr(image_bytes: bytes) -> Tuple[Any, Dict[str, Any]]:
    """
    Görsel ön işleme hattı (Image Preprocessing Pipeline):
    - Boyut ölçekleme (Upscaling): Düşük çözünürlüklü görselleri (genişlik < 1200px) 1.5x - 2x büyütür.
    - Grayscale dönüşümü
    - Kontrast ve Keskinlik artırma (Contrast & Sharpness Enhancement)
    - Denoise / Gürültü azaltma
    """
    from PIL import Image, ImageEnhance
    
    image = Image.open(io.BytesIO(image_bytes))
    orig_w, orig_h = image.size
    
    metadata = {
        "original_width": orig_w,
        "original_height": orig_h,
        "preprocessed": True,
        "scale_factor": 1.0
    }
    
    # 1. Küçük görselleri büyüt (OCR doğruluğu için 1200px+ ideal)
    if orig_w < 1200:
        scale = min(2.5, 1400 / max(orig_w, 1))
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resample_method = getattr(Image, 'Resampling', Image).LANCZOS
        image = image.resize((new_w, new_h), resample_method)
        metadata["scale_factor"] = round(scale, 2)
        metadata["processed_width"] = new_w
        metadata["processed_height"] = new_h
        
    # 2. Grayscale Dönüşümü
    if image.mode != "L":
        image = image.convert("L")
        
    # 3. Kontrast ve Keskinlik Artırma
    contrast_enhancer = ImageEnhance.Contrast(image)
    image = contrast_enhancer.enhance(1.6)
    
    sharpness_enhancer = ImageEnhance.Sharpness(image)
    image = sharpness_enhancer.enhance(1.8)
    
    return image, metadata

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
        "Extract all readable text, titles, numbers, tables, MRZ lines, and notes from this document/image verbatim. "
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
    Ön işlenmiş görsel ve pytesseract kullanarak yerel OCR uygular.
    """
    try:
        import pytesseract

        _configure_tesseract()
        processed_image, _ = preprocess_image_for_ocr(image_bytes)

        # Tesseract dilleri dene (tur+eng veya varsayılan eng)
        try:
            text = pytesseract.image_to_string(processed_image, lang="tur+eng")
        except Exception:
            text = pytesseract.image_to_string(processed_image)
            
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

def extract_text_from_image_bytes(
    image_bytes: bytes, 
    mime_type: str = "image/jpeg",
    return_metadata: bool = False
) -> Union[Tuple[str, str], Tuple[str, str, Dict[str, Any]]]:
    """
    Verilen görsel baytlarından metin ayıklar.
    Önce Groq Vision modelini dener; ardından Tesseract OCR motoruna geçer.
    
    Dönüş: (metin, extraction_method) veya (metin, extraction_method, metadata)
    """
    if not image_bytes:
        raise ValueError("Görsel verisi boş.")

    if not validate_image_magic_bytes(image_bytes):
        raise ValueError("Geçersiz görsel formatı (Magic Byte doğrulanamadı). Güvenlik nedeniyle işlem durduruldu.")

    metadata: Dict[str, Any] = {"mime_type": mime_type}

    # 1. Groq Vision LLM ile dene (eğer yapılandırılmışsa)
    if _is_groq_vision_available():
        vision_text = extract_text_with_vision_llm(image_bytes, mime_type=mime_type)
        if vision_text and vision_text.strip():
            metadata["engine"] = "groq_vision"
            metadata["confidence_estimate"] = "VERY_HIGH"
            if return_metadata:
                return vision_text.strip(), "vision_ocr", metadata
            return vision_text.strip(), "vision_ocr"

    # 2. Yerel Tesseract OCR ile dene (Ön İşleme Hattı ile)
    tesseract_text = extract_text_with_tesseract(image_bytes)
    metadata["engine"] = "tesseract_ocr"
    
    if tesseract_text and tesseract_text.strip():
        metadata["confidence_estimate"] = "HIGH" if len(tesseract_text) > 100 else "MEDIUM"
        if return_metadata:
            return tesseract_text.strip(), "tesseract_ocr", metadata
        return tesseract_text.strip(), "tesseract_ocr"

    raise ValueError(
        "Görsel veya taranmış dokümandan metin okunamadı. "
        "Görsel çok düşük çözünürlüklü olabilir veya OCR motoruna erişilemiyor olabilir."
    )

from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import TextAnalysisRequest, AnalysisResponse
from app.utils.text_cleaner import clean_text
from app.utils.language_detector import detect_language, get_language_label
from app.services.summary_service import generate_summary
from app.services.keyword_service import extract_keywords
from app.services.category_service import predict_category
from app.services.risk_service import analyze_risk
from app.services.pdf_service import extract_text_from_pdf
from app.services.ocr_service import extract_text_from_image_bytes

router = APIRouter()

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tiff": "image/tiff",
    ".bmp": "image/bmp"
}

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "AI Analysis Service is running!"}

def process_text_pipeline(
    raw_text: str, 
    req_language: Optional[str] = None,
    extraction_method: str = "text",
    page_count: Optional[int] = None
) -> AnalysisResponse:
    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="Metin içeriği boş olamaz.")
        
    cleaned_text = clean_text(raw_text)
    
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Metin içeriği geçerli karakter barındırmıyor.")

    try:
        lang_code = req_language if req_language and req_language.strip() else detect_language(cleaned_text)
        lang_label = get_language_label(lang_code)
        
        summary = generate_summary(cleaned_text, language=lang_code)
        keywords = extract_keywords(cleaned_text, language=lang_code)
        category = predict_category(cleaned_text)
        risk_data = analyze_risk(cleaned_text)

        return AnalysisResponse(
            summary=summary,
            keywords=keywords,
            category=category,
            risk_level=risk_data["risk_level"],
            risk_score=risk_data["risk_score"],
            language=lang_code,
            language_label=lang_label,
            extraction_method=extraction_method,
            page_count=page_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz sırasında bir sunucu hatası oluştu: {str(e)}")

@router.post("/analyze-text", response_model=AnalysisResponse)
def analyze_text(request: TextAnalysisRequest):
    return process_text_pipeline(request.text, req_language=request.language, extraction_method="text")

@router.post("/analyze-pdf", response_model=AnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir PDF dosyası yükleyin.")
    
    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Yüklenen PDF dosyası boş.")
            
        raw_text, method, page_count = extract_text_from_pdf(file_bytes, return_metadata=True)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF dosyası okunamadı: {str(e)}")
        
    if not raw_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="PDF dosyasından metin çıkarılamadı. Dosya boş veya okunamaz durumda olabilir."
        )
    
    return process_text_pipeline(raw_text, extraction_method=method, page_count=page_count)

@router.post("/analyze-image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    ext = next((e for e in SUPPORTED_IMAGE_EXTENSIONS if filename.endswith(e)), None)
    
    if not ext:
        supported = ", ".join(SUPPORTED_IMAGE_EXTENSIONS.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Desteklenmeyen görsel formatı. Lütfen şu formatlardan birini yükleyin: {supported}"
        )
        
    mime_type = SUPPORTED_IMAGE_EXTENSIONS[ext]
    
    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Yüklenen görsel dosyası boş.")
            
        raw_text, method = extract_text_from_image_bytes(file_bytes, mime_type=mime_type)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Görsel işlenirken hata oluştu: {str(e)}")
        
    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Görsel üzerinden okunabilir metin çıkarılamadı."
        )
        
    return process_text_pipeline(raw_text, extraction_method=method)
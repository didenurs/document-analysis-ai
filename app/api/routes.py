from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import (
    TextAnalysisRequest, 
    AnalysisResponse, 
    TranslationRequest, 
    TranslationResponse,
    ChatDocumentRequest,
    ChatDocumentResponse,
    MaskRequest,
    MaskResponse,
    PIIEntity,
    KVKKReport
)
from app.utils.text_cleaner import clean_text
from app.utils.language_detector import detect_language, get_language_label
from app.services.summary_service import generate_summary
from app.services.keyword_service import extract_keywords
from app.services.category_service import predict_category
from app.services.risk_service import analyze_risk
from app.services.pdf_service import extract_text_from_pdf
from app.services.ocr_service import extract_text_from_image_bytes
from app.services.llm_service import translate_text
from app.services.rag_service import generate_rag_answer
from app.services.ner_service import mask_pii_text

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
        
        # Faz 3: KVKK & Kişisel Veri Maskeleme
        masked_txt, entity_dicts, kvkk_dict = mask_pii_text(cleaned_text, mask_mode="starred")
        
        pii_entities = [
            PIIEntity(
                type=e["type"],
                text=e["text"],
                label=e["label"],
                masked_value=e["masked_value"],
                start=e.get("start"),
                end=e.get("end")
            )
            for e in entity_dicts
        ]
        
        kvkk_rep = KVKKReport(
            status=kvkk_dict["status"],
            risk_level=kvkk_dict["risk_level"],
            total_entities=kvkk_dict["total_entities"],
            breakdown=kvkk_dict["breakdown"]
        )

        return AnalysisResponse(
            summary=summary,
            keywords=keywords,
            category=category,
            risk_level=risk_data["risk_level"],
            risk_score=risk_data["risk_score"],
            language=lang_code,
            language_label=lang_label,
            extraction_method=extraction_method,
            page_count=page_count,
            cleaned_text=cleaned_text,
            entities=pii_entities,
            masked_text=masked_txt,
            kvkk_report=kvkk_rep
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

@router.post("/translate", response_model=TranslationResponse)
def translate_endpoint(request: TranslationRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Çevrilecek metin boş olamaz.")
        
    target_lang = request.target_language.lower()
    if target_lang not in ["tr", "en"]:
        raise HTTPException(status_code=400, detail="Desteklenen hedef diller: 'tr', 'en'")
        
    target_label = "Türkçe" if target_lang == "tr" else "English"
    translated = translate_text(request.text, target_language=target_lang)
    
    if not translated:
        raise HTTPException(
            status_code=500, 
            detail="Metin çevrilirken bir hata oluştu. Lütfen geçerli bir LLM API anahtarı sağlandığından emin olun."
        )
        
    return TranslationResponse(
        original_text=request.text,
        translated_text=translated,
        target_language=target_lang,
        target_language_label=target_label
    )

@router.post("/chat-document", response_model=ChatDocumentResponse)
def chat_document_endpoint(request: ChatDocumentRequest):
    if not request.document_text or not request.document_text.strip():
        raise HTTPException(status_code=400, detail="Doküman metni boş olamaz.")
        
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Soru metni boş olamaz.")

    history_dicts = []
    if request.history:
        for msg in request.history:
            history_dicts.append({"role": msg.role, "content": msg.content})

    try:
        rag_result = generate_rag_answer(
            document_text=request.document_text,
            question=request.question,
            history=history_dicts,
            language=request.language
        )
        return ChatDocumentResponse(
            answer=rag_result["answer"],
            sources=rag_result["sources"],
            confidence=rag_result["confidence"],
            language=rag_result["language"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Soru yanıtlanırken bir hata oluştu: {str(e)}")

@router.post("/mask-pii", response_model=MaskResponse)
def mask_pii_endpoint(request: MaskRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Maskelenecek metin boş olamaz.")
        
    mode = request.mask_mode if request.mask_mode in ["starred", "redact", "tag"] else "starred"
    masked_txt, entity_dicts, kvkk_dict = mask_pii_text(request.text, mask_mode=mode)
    
    pii_entities = [
        PIIEntity(
            type=e["type"],
            text=e["text"],
            label=e["label"],
            masked_value=e["masked_value"],
            start=e.get("start"),
            end=e.get("end")
        )
        for e in entity_dicts
    ]
    
    kvkk_rep = KVKKReport(
        status=kvkk_dict["status"],
        risk_level=kvkk_dict["risk_level"],
        total_entities=kvkk_dict["total_entities"],
        breakdown=kvkk_dict["breakdown"]
    )
    
    return MaskResponse(
        original_text=request.text,
        masked_text=masked_txt,
        entities=pii_entities,
        kvkk_report=kvkk_rep
    )
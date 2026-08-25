import os
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
from app.services.category_service import predict_category, get_category_label
from app.services.risk_service import analyze_risk
from app.services.pdf_service import extract_text_from_pdf
from app.services.ocr_service import extract_text_from_image_bytes
from app.services.llm_service import translate_text
from app.services.rag_service import generate_rag_answer
from app.services.ner_service import mask_pii_text, detect_pii_entities

from app.services.anomaly_service import detect_document_anomalies
from app.services.recommendation_service import generate_action_recommendations
from app.services.metrics_service import record_analysis_metrics, get_system_metrics
from app.services.webhook_service import dispatch_webhook_event
from app.services.cv_service import analyze_cv_document
from app.models.schemas import WebhookTestRequest, SystemMetricsResponse

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
        # Faz 3: KVKK & Kişisel Veri Maskeleme (Privacy by Design)
        masked_txt, entity_dicts, kvkk_dict = mask_pii_text(cleaned_text, mask_mode="starred")
        
        lang_code = req_language if req_language and req_language.strip() else detect_language(cleaned_text)
        lang_label = get_language_label(lang_code)
        
        # LLM ve Özet motoruna maskelenmiş metin gönderilir
        raw_summary = generate_summary(masked_txt, language=lang_code)
        
        # Çıktı özetini de PII filtresinden geçir (Çift Katmanlı Koruma)
        summary, _, _ = mask_pii_text(raw_summary, mask_mode="starred")
        
        keywords = extract_keywords(masked_txt, language=lang_code)
        category = predict_category(cleaned_text)  # Ham metin üzerinde kategori tespiti
        category_lbl = get_category_label(category)

        # Üç boyutlu risk: PII varlıkları risk motoruna iletiliyor
        risk_data = analyze_risk(
            text=cleaned_text,
            category=category,
            pii_entities=entity_dicts,
        )

        pii_entities = [
            PIIEntity(
                type=e["type"],
                text=e["text"],
                label=e["label"],
                masked_value=e["masked_value"],
                start=e.get("start"),
                end=e.get("end"),
                confidence_score=e.get("confidence_score", 1.0)
            )
            for e in entity_dicts
        ]
        
        kvkk_rep = KVKKReport(
            status=kvkk_dict["status"],
            risk_level=kvkk_dict["risk_level"],
            kvkk_risk_label=kvkk_dict.get("kvkk_risk_label"),
            total_entities=kvkk_dict["total_entities"],
            breakdown=kvkk_dict["breakdown"],
            confidence_warnings=kvkk_dict.get("confidence_warnings", [])
        )

        # ── Maskeleme Sonrası İkinci PII Tarama (Residual Scan) ────────────────
        residual_entities = detect_pii_entities(masked_txt)
        detected_count = len(entity_dicts)
        residual_count = len(residual_entities)
        masked_count = max(0, detected_count - residual_count)
        coverage = round((masked_count / detected_count * 100), 1) if detected_count > 0 else 100.0
        redaction_verification = {
            "detected": detected_count,
            "masked": masked_count,
            "residual": residual_count,
            "coverage_percent": coverage,
            "status": "VERIFIED" if residual_count == 0 else "INCOMPLETE",
            "residual_entities": [
                {"type": r["type"], "label": r["label"]} for r in residual_entities
            ],
        }

        # Faz 5: Anomali & Sahtecilik Tespiti
        anomaly_rep = detect_document_anomalies(cleaned_text, category=category)

        # Faz 5: Otomatik Aksiyon Önerileri Motoru
        recs = generate_action_recommendations(
            category=category,
            risk_level=risk_data["risk_level"],
            risk_score=risk_data["risk_score"],
            kvkk_report=kvkk_rep,
            anomaly_report=anomaly_rep
        )

        # Faz 5: Canlı Sistem Metriklerini Güncelle
        record_analysis_metrics(
            category=category,
            risk_score=risk_data["risk_score"],
            pii_count=kvkk_dict["total_entities"]
        )

        cv_info = analyze_cv_document(cleaned_text)

        return AnalysisResponse(
            summary=summary,
            keywords=keywords,
            category=category,
            category_label=category_lbl,
            risk_level=risk_data["risk_level"],
            risk_score=risk_data["risk_score"],
            risk_breakdown=risk_data.get("risk_breakdown"),
            language=lang_code,
            language_label=lang_label,
            extraction_method=extraction_method,
            page_count=page_count,
            cleaned_text=cleaned_text,
            entities=pii_entities,
            masked_text=masked_txt,
            kvkk_report=kvkk_rep,
            anomaly_report=anomaly_rep,
            recommendations=recs,
            cv_analysis=cv_info if cv_info.get("is_cv") else None,
            redaction_verification=redaction_verification,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz sırasında bir sunucu hatası oluştu: {str(e)}")


@router.post("/analyze-text", response_model=AnalysisResponse)
def analyze_text(request: TextAnalysisRequest):
    return process_text_pipeline(request.text, req_language=request.language, extraction_method="text")

def sanitize_filename(filename: Optional[str]) -> str:
    """Path traversal (../) ve null-byte karakterleri temizler."""
    if not filename:
        return "unnamed_file"
    clean_name = os.path.basename(filename).replace("\x00", "").replace("..", "").strip()
    return clean_name or "unnamed_file"

@router.post("/analyze-pdf", response_model=AnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    safe_filename = sanitize_filename(file.filename)
    if not safe_filename.lower().endswith('.pdf'):
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

# --- FAZ 4 ENDPOINT'LERİ (Toplu Analiz, Doküman Karşılaştırma & Export) ---

from typing import List as ListType
from fastapi import Response
from app.models.schemas import (
    BatchAnalysisResponse,
    DocumentCompareRequest,
    DocumentCompareResponse,
    ExportRequest
)
from app.services.batch_service import aggregate_batch_results
from app.services.compare_service import compare_two_documents
from app.services.export_service import generate_json_bytes, generate_csv_bytes, generate_html_report, generate_pdf_report, generate_masked_pdf_report

@router.post("/analyze-batch", response_model=BatchAnalysisResponse)
async def analyze_batch_files(files: ListType[UploadFile] = File(...)):
    """
    Birden fazla dosyayı (PDF, Görsel, TXT) eşzamanlı olarak işler ve toplu analiz raporu döndürür.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="En az 1 adet dosya yüklenmelidir.")
        
    processed_items = []
    
    for file in files:
        filename = file.filename or "unknown_file"
        lower_name = filename.lower()
        
        try:
            file_bytes = await file.read()
            if len(file_bytes) == 0:
                continue
                
            if lower_name.endswith('.pdf'):
                raw_text, method, page_count = extract_text_from_pdf(file_bytes, return_metadata=True)
            elif any(lower_name.endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS):
                ext = next(e for e in SUPPORTED_IMAGE_EXTENSIONS if lower_name.endswith(e))
                mime_type = SUPPORTED_IMAGE_EXTENSIONS[ext]
                raw_text, method = extract_text_from_image_bytes(file_bytes, mime_type=mime_type)
                page_count = 1
            else:
                # Düz metin / TXT dosyası kabul edilir
                raw_text = file_bytes.decode('utf-8', errors='ignore')
                method = "text"
                page_count = 1
                
            if raw_text and raw_text.strip():
                resp = process_text_pipeline(
                    raw_text,
                    extraction_method=method,
                    page_count=page_count
                )
                processed_items.append((filename, resp))
        except Exception as e:
            # Hatalı dosyalar atlanır veya genel havuza eklenmez
            continue
            
    if not processed_items:
        raise HTTPException(
            status_code=400,
            detail="Yüklenen dosyaların hiçbirinden okunabilir metin çıkarılamadı."
        )

    return aggregate_batch_results(processed_items)

@router.post("/compare-documents", response_model=DocumentCompareResponse)
def compare_documents_endpoint(request: DocumentCompareRequest):
    """
    İki dokümanı karşılaştırarak benzerlik skorunu, risk değişimini ve PII farkını çıkarır.
    """
    if not request.doc1_text or not request.doc1_text.strip():
        raise HTTPException(status_code=400, detail="1. Doküman metni boş olamaz.")
    if not request.doc2_text or not request.doc2_text.strip():
        raise HTTPException(status_code=400, detail="2. Doküman metni boş olamaz.")
        
    return compare_two_documents(
        doc1_text=request.doc1_text,
        doc2_text=request.doc2_text,
        doc1_title=request.doc1_title or "Doküman 1",
        doc2_title=request.doc2_title or "Doküman 2",
        language=request.language
    )

@router.post("/export/json")
def export_json_endpoint(request: ExportRequest):
    """Analiz sonuçlarını indirilebilir JSON olarak verir."""
    json_bytes = generate_json_bytes(request.analysis_data)
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=doc_analysis_report.json"}
    )

@router.post("/export/csv")
def export_csv_endpoint(request: ExportRequest):
    """Analiz sonuçlarını indirilebilir CSV e-tablo dosyası olarak verir."""
    csv_bytes = generate_csv_bytes(request.analysis_data)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=doc_analysis_report.csv"}
    )

@router.post("/export/html")
def export_html_endpoint(request: ExportRequest):
    """Analiz sonuçlarını baskıya uygun (PDF-ready) HTML raporu olarak verir."""
    html_content = generate_html_report(request.analysis_data)
    return Response(
        content=html_content.encode('utf-8'),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=doc_analysis_report.html"}
    )

@router.post("/export/pdf")
def export_pdf_endpoint(request: ExportRequest):
    """Analiz sonuçlarını ve maskelenmiş metni doğrudan .PDF belgesi olarak indirilebilir kılar."""
    pdf_bytes = generate_pdf_report(request.analysis_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=doc_analysis_report.pdf"}
    )

@router.post("/export/masked-pdf")
def export_masked_pdf_endpoint(request: ExportRequest):
    """Kişisel verileri maskelenmiş dokümanı doğrudan tek tıkla indirilebilir .PDF dosyası olarak verir."""
    pdf_bytes = generate_masked_pdf_report(request.analysis_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=maskelenmis_dokuman.pdf"}
    )


# --- FAZ 5 ENDPOINT'LERİ (Anomali, Akıllı Aksiyon Motoru, Metrikler & Webhook) ---

@router.get("/metrics", response_model=SystemMetricsResponse)
@router.get("/analytics", response_model=SystemMetricsResponse)
def get_metrics_endpoint():
    """Sistem geneli işleme istatistiklerini ve canlı metrikleri döndürür."""
    return get_system_metrics()

@router.post("/webhooks/test")
async def test_webhook_endpoint(request: WebhookTestRequest):
    """Belirtilen Webhook URL adresine canlı test bildirimi gönderir."""
    sample_payload = {
        "event": request.event_type or "risk.critical",
        "sample_document": "Güvenlik Test Dokümanı",
        "risk_score": 85,
        "message": "Dokümanda kritik risk uyarısı tespit edilmiştir."
    }
    res = await dispatch_webhook_event(request.webhook_url, request.event_type or "risk.critical", sample_payload)
    return res
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TextAnalysisRequest(BaseModel):
    text: str
    language: Optional[str] = None

class PIIEntity(BaseModel):
    type: str
    text: str
    label: str
    masked_value: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence_score: Optional[float] = 1.0

class KVKKReport(BaseModel):
    status: str
    risk_level: str
    total_entities: int
    breakdown: Dict[str, int]
    confidence_warnings: Optional[List[str]] = []

class AnomalyReport(BaseModel):
    has_anomaly: bool
    anomaly_score: int
    anomaly_flags: List[str]
    details: str

class ActionItem(BaseModel):
    priority: str  # "High", "Medium", "Low"
    category: str  # "Security", "Compliance", "Legal", "Operational"
    title: str
    description: str

class AnalysisResponse(BaseModel):
    summary: str
    keywords: List[str]
    category: str
    risk_level: str
    risk_score: int
    language: Optional[str] = "en"
    language_label: Optional[str] = "English"
    extraction_method: Optional[str] = "text"
    page_count: Optional[int] = None
    cleaned_text: Optional[str] = None
    entities: Optional[List[PIIEntity]] = []
    masked_text: Optional[str] = None
    kvkk_report: Optional[KVKKReport] = None
    anomaly_report: Optional[AnomalyReport] = None
    recommendations: Optional[List[ActionItem]] = []
    cv_analysis: Optional[Dict[str, Any]] = None


class TranslationRequest(BaseModel):
    text: str
    target_language: str = "tr"  # "tr" veya "en"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_language: str
    target_language_label: str

class ChatMessage(BaseModel):
    role: str  # "user" veya "assistant"
    content: str

class ChatDocumentRequest(BaseModel):
    document_text: str
    question: str
    history: Optional[List[ChatMessage]] = None
    language: Optional[str] = None

class ChatDocumentResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float
    language: str

class MaskRequest(BaseModel):
    text: str
    mask_mode: Optional[str] = "starred"  # "starred", "redact", "tag"

class MaskResponse(BaseModel):
    original_text: str
    masked_text: str
    entities: List[PIIEntity]
    kvkk_report: KVKKReport

# --- FAZ 4 MODELLERİ (Toplu Analiz, Doküman Karşılaştırma & Export) ---

class BatchAnalysisItem(BaseModel):
    filename: str
    extraction_method: str = "text"
    page_count: Optional[int] = None
    analysis: AnalysisResponse

class BatchAnalysisResponse(BaseModel):
    total_documents: int
    overall_summary: str
    global_risk_level: str
    global_risk_score: int
    global_kvkk_report: KVKKReport
    documents: List[BatchAnalysisItem]

class DocumentCompareRequest(BaseModel):
    doc1_text: str
    doc2_text: str
    doc1_title: Optional[str] = "Doküman 1"
    doc2_title: Optional[str] = "Doküman 2"
    language: Optional[str] = None

class DocumentCompareResponse(BaseModel):
    similarity_score: float
    similarity_percentage: int
    risk_delta: int
    risk_status: str
    added_keypoints: List[str]
    removed_keypoints: List[str]
    doc1_category: str
    doc2_category: str
    doc1_risk_score: int
    doc2_risk_score: int
    pii_diff_count: int
    summary_comparison: str

class ExportRequest(BaseModel):
    analysis_data: Dict[str, Any]
    export_format: Optional[str] = "json"  # "json", "csv", "html"

# --- FAZ 5 MODELLERİ (Anomali, Tavsiye Motoru, Webhook & Metrikler) ---

class WebhookTestRequest(BaseModel):
    webhook_url: str
    event_type: Optional[str] = "risk.critical"

class SystemMetricsResponse(BaseModel):
    total_processed: int
    total_pii_masked: int
    avg_risk_score: float
    category_breakdown: Dict[str, int]
    system_status: str
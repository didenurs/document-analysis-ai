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

class KVKKReport(BaseModel):
    status: str
    risk_level: str
    total_entities: int
    breakdown: Dict[str, int]

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
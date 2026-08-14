from pydantic import BaseModel
from typing import List, Optional

class TextAnalysisRequest(BaseModel):
    text: str
    language: Optional[str] = None

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

class TranslationRequest(BaseModel):
    text: str
    target_language: str = "tr"  # "tr" veya "en"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_language: str
    target_language_label: str
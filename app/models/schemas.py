from pydantic import BaseModel
from typing import List

class TextAnalysisRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    summary: str
    keywords: List[str]
    category: str
    risk_level: str
    risk_score: int
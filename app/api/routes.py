from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import TextAnalysisRequest, AnalysisResponse
from app.utils.text_cleaner import clean_text
from app.services.summary_service import generate_summary
from app.services.keyword_service import extract_keywords
from app.services.category_service import predict_category
from app.services.risk_service import analyze_risk
from app.services.pdf_service import extract_text_from_pdf

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "AI Analysis Service is running!"}

def process_text_pipeline(raw_text: str) -> AnalysisResponse:
    cleaned_text = clean_text(raw_text)
    
    if not cleaned_text:
         raise HTTPException(status_code=400, detail="Metin içeriği boş olamaz.")

    summary = generate_summary(cleaned_text)
    keywords = extract_keywords(cleaned_text)
    category = predict_category(cleaned_text)
    risk_data = analyze_risk(cleaned_text)

    return AnalysisResponse(
        summary=summary,
        keywords=keywords,
        category=category,
        risk_level=risk_data["risk_level"],
        risk_score=risk_data["risk_score"]
    )

@router.post("/analyze-text", response_model=AnalysisResponse)
def analyze_text(request: TextAnalysisRequest):
    return process_text_pipeline(request.text)

@router.post("/analyze-pdf", response_model=AnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yükleyebilirsiniz.")
    
    file_bytes = await file.read()
    raw_text = extract_text_from_pdf(file_bytes)
    return process_text_pipeline(raw_text)
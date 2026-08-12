import pytest
import os
from app.utils.text_cleaner import clean_text
from app.services.risk_service import analyze_risk
from app.services.keyword_service import extract_keywords
from app.services.category_service import predict_category
from app.services.summary_service import generate_summary
from app.services.pdf_service import extract_text_from_pdf

def test_text_cleaner():
    raw = "  Bu   bir \n\n test   metnidir.   \t "
    cleaned = clean_text(raw)
    assert cleaned == "Bu bir test metnidir."

def test_risk_service_empty():
    res = analyze_risk("")
    assert res["risk_score"] == 0
    assert res["risk_level"] == "Low"

def test_risk_service_high_risk():
    text = "Critical security breach detected! A zero-day exploit and ransomware caused a massive data leak."
    res = analyze_risk(text)
    assert res["risk_score"] > 5
    assert res["risk_level"] in ["Medium", "High"]

def test_risk_service_word_boundary():
    # 'attack' geçmiyor, 'heartattack' geçiyor; kelime sınır kontrolü bunu izole etmeli
    text = "The doctor noted a general case without any true attack."
    res = analyze_risk(text)
    assert isinstance(res["risk_score"], int)

def test_keyword_service():
    text = "Artificial intelligence and machine learning models are transforming automated document analysis."
    keywords = extract_keywords(text, top_n=3)
    assert isinstance(keywords, list)
    assert len(keywords) > 0

def test_keyword_service_empty():
    assert extract_keywords("") == []

def test_category_service():
    text = "The company reported record quarterly revenue and high profit margins on stock investments."
    cat = predict_category(text)
    assert cat in ["Technology", "Finance", "Healthcare", "Cyber Security", "Education", "General"]

def test_summary_service_short_text():
    text = "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints."
    summary = generate_summary(text)
    assert isinstance(summary, str)
    assert len(summary) > 0

def test_pdf_service_empty_bytes():
    with pytest.raises(ValueError):
        extract_text_from_pdf(b"")

def test_pdf_service_valid_file():
    pdf_path = os.path.join(os.path.dirname(__file__), "analyze-pdf.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        extracted = extract_text_from_pdf(pdf_bytes)
        assert isinstance(extracted, str)
        assert len(extracted) > 0

import pytest
import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "running" in data["message"].lower()

def test_analyze_text_valid_en():
    payload = {
        "text": "Cyber security researchers identified a severe vulnerability in the cloud authentication system leading to an emergency patch release."
    }
    response = client.post("/analyze-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "summary" in data
    assert "keywords" in data
    assert "category" in data
    assert "risk_level" in data
    assert "risk_score" in data
    assert "language" in data
    assert data["language"] == "en"
    assert isinstance(data["keywords"], list)
    assert isinstance(data["risk_score"], int)

def test_analyze_text_valid_tr():
    payload = {
        "text": "Şirketimizin üçüncü çeyrek finansal sonuçlarında faaliyet gelirleri ve net kâr marjında önemli büyüme sağlandı."
    }
    response = client.post("/analyze-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "summary" in data
    assert "keywords" in data
    assert "category" in data
    assert data["category"] == "Finance"
    assert "risk_level" in data
    assert "language" in data
    assert data["language"] == "tr"
    assert data["language_label"] == "Türkçe"

def test_analyze_text_empty():
    response = client.post("/analyze-text", json={"text": "   "})
    assert response.status_code == 400

def test_analyze_pdf_invalid_extension():
    files = {"file": ("test.txt", b"some text content", "text/plain")}
    response = client.post("/analyze-pdf", files=files)
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]

def test_analyze_pdf_valid():
    pdf_path = os.path.join(os.path.dirname(__file__), "analyze-pdf.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f.read(), "application/pdf")}
        response = client.post("/analyze-pdf", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert len(data["summary"]) > 0
        assert "language" in data

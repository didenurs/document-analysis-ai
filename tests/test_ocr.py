import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw
import pymupdf as fitz
from fastapi.testclient import TestClient

from app.main import app
from app.services.ocr_service import extract_text_from_image_bytes, extract_text_with_vision_llm
from app.services.pdf_service import extract_text_from_pdf

client = TestClient(app)

def create_sample_image_bytes(text: str = "CONFIDENTIAL SECURITY REPORT") -> bytes:
    """Bellekte basit bir metin görseli oluşturur."""
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_scanned_pdf_bytes(text: str = "SCANNED INCIDENT DATA") -> bytes:
    """Metin içermeyen, sadece görsel yerleştirilmiş bir taranmış PDF oluşturur."""
    img_bytes = create_sample_image_bytes(text)
    doc = fitz.open()
    page = doc.new_page(width=400, height=100)
    page.insert_image(fitz.Rect(0, 0, 400, 100), stream=img_bytes)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_ocr_service_empty_bytes():
    with pytest.raises(ValueError):
        extract_text_from_image_bytes(b"")

def test_ocr_service_groq_vision_mock():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Zero-day vulnerability detected in cloud firewall."}}
        ]
    }
    
    img_bytes = create_sample_image_bytes()
    with patch("app.services.ocr_service._is_groq_vision_available", return_value=True):
        with patch("httpx.Client.post", return_value=mock_response):
            text, method = extract_text_from_image_bytes(img_bytes)
            assert "vulnerability" in text.lower()
            assert method == "vision_ocr"

def test_ocr_service_tesseract_mock():
    img_bytes = create_sample_image_bytes()
    with patch("app.services.ocr_service._is_groq_vision_available", return_value=False):
        with patch("app.services.ocr_service.extract_text_with_tesseract", return_value="Quarterly financial growth report with profits."):
            text, method = extract_text_from_image_bytes(img_bytes)
            assert "growth" in text.lower()
            assert method == "tesseract_ocr"

def test_analyze_image_endpoint_invalid_format():
    files = {"file": ("document.txt", b"Not an image", "text/plain")}
    response = client.post("/analyze-image", files=files)
    assert response.status_code == 400
    assert "Desteklenmeyen" in response.json()["detail"]

def test_analyze_image_endpoint_success():
    img_bytes = create_sample_image_bytes()
    files = {"file": ("report.png", img_bytes, "image/png")}
    
    with patch("app.api.routes.extract_text_from_image_bytes", return_value=("Critical server breach occurred during maintenance.", "vision_ocr")):
        response = client.post("/analyze-image", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "risk_score" in data
        assert data["extraction_method"] == "vision_ocr"

def test_hybrid_pdf_extraction_scanned_page():
    pdf_bytes = create_scanned_pdf_bytes("EMERGENCY ATTACK ALERT")
    
    with patch("app.services.pdf_service.extract_text_from_image_bytes", return_value=("Emergency attack alert and system failure.", "vision_ocr")):
        extracted, method, page_count = extract_text_from_pdf(pdf_bytes, return_metadata=True)
        assert "Emergency attack alert" in extracted
        assert method == "ocr"
        assert page_count == 1

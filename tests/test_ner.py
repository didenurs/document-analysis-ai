import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ner_service import is_valid_tckn, detect_pii_entities, mask_pii_text, calculate_kvkk_report

client = TestClient(app)

SAMPLE_PII_TEXT = """
MÜŞTERİ BİLGİSİ: Sayın Ahmet Yılmaz, 10000000146 numaralı TCKN ve TR12 3456 7890 1234 5678 9012 34 nolu IBAN kaydınız bulunmaktadır.
İletişim: ahmet.yilmaz@sirket.com veya 0532 123 45 67.
Sunucu IP: 192.168.1.50 ve API Key: gsk_1234567890abcdef1234567890abcdef.
Kredi kartı: 4543 1234 5678 9012.
"""

def test_tckn_validation():
    # 10000000146 geçerli bir örnek TCKN'dir
    assert is_valid_tckn("10000000146") is True
    # Geçersiz TCKN'ler
    assert is_valid_tckn("12345678901") is False
    assert is_valid_tckn("01234567890") is False
    assert is_valid_tckn("12345") is False

def test_detect_pii_entities():
    entities = detect_pii_entities(SAMPLE_PII_TEXT)
    types = [e["type"] for e in entities]
    
    assert "TCKN" in types
    assert "IBAN" in types
    assert "EMAIL" in types
    assert "PHONE" in types
    assert "IP_ADDRESS" in types
    assert "API_KEY" in types
    assert "CREDIT_CARD" in types
    assert "NAME" in types

def test_mask_pii_text_modes():
    # 1. Starred (*) modu
    masked_starred, entities, report = mask_pii_text(SAMPLE_PII_TEXT, mask_mode="starred")
    assert "10000000146" not in masked_starred
    assert "100*****46" in masked_starred
    assert "ah***@sirket.com" in masked_starred
    assert "192.168.*.*" in masked_starred
    assert report["risk_level"] == "High"

    # 2. Redact modu
    masked_redact, _, _ = mask_pii_text(SAMPLE_PII_TEXT, mask_mode="redact")
    assert "[TCKN_MASKELENDİ]" in masked_redact
    assert "[E-POSTA_MASKELENDİ]" in masked_redact
    assert "[IP ADRESİ_MASKELENDİ]" in masked_redact

    # 3. Tag modu
    masked_tag, _, _ = mask_pii_text(SAMPLE_PII_TEXT, mask_mode="tag")
    assert "<TCKN>" in masked_tag
    assert "<EMAIL>" in masked_tag

def test_calculate_kvkk_report_safe():
    safe_text = "Bu genel bir şirket bilgilendirme metnidir. Herhangi bir kişisel veri bulunmamaktadır."
    entities = detect_pii_entities(safe_text)
    report = calculate_kvkk_report(entities)
    assert report["total_entities"] == 0
    assert report["risk_level"] == "Low"
    assert "Güvenli" in report["status"]

def test_mask_pii_endpoint_success():
    payload = {
        "text": "Sayın Mehmet Demir, lütfen mehm@test.com ve 0544 111 22 33 üzerinden arayınız.",
        "mask_mode": "starred"
    }
    response = client.post("/mask-pii", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "masked_text" in data
    assert "me***@test.com" in data["masked_text"]
    assert len(data["entities"]) >= 2
    assert "kvkk_report" in data

def test_mask_pii_endpoint_empty():
    response = client.post("/mask-pii", json={"text": "   "})
    assert response.status_code == 400

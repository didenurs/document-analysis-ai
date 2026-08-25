import pytest
from app.services.ner_service import is_valid_iban, detect_pii_entities, mask_pii_text
from app.services.pdf_service import extract_text_from_pdf
from app.services.ocr_service import validate_image_magic_bytes
from app.services.webhook_service import is_safe_webhook_url
from app.services.risk_service import analyze_risk
from app.services.cv_service import analyze_cv_document, is_cv_document

def test_iban_validation():
    # Geçerli Türkiye IBAN örneği (ISO 7064 Mod 97-10)
    assert is_valid_iban("TR40 0006 2000 0000 0000 0000 01") is True
    # Geçersiz IBAN
    assert is_valid_iban("INVALID_IBAN_STRING_123") is False
    assert is_valid_iban("TR99 9999 9999 9999 9999 9999 99") is False

def test_new_pii_entities_detection():
    sample_text = """
    Sayın Ahmet Yılmaz, Doğum Tarihi: 15.08.1992, Araç Plakası: 34 ABC 123, 
    Kimlik Seri No: A12B34567, Anne Adı: Ayşe. 
    Biyometrik veri kullanımı ve parmak izi uygulaması yapılmaktadır. MRZ: I<TUR123456789<<<<<<<<<<<<<<<
    """
    entities = detect_pii_entities(sample_text)
    types = [e["type"] for e in entities]

    assert "BIRTH_DATE" in types
    assert "LICENSE_PLATE" in types
    assert "SERIAL_NO" in types
    assert "BIOMETRIC_NOTICE" in types
    assert "MRZ" in types

def test_pdf_magic_bytes_invalid():
    fake_pdf = b"NOT_A_PDF_HEADER_THIS_IS_EVIL_EXEC"
    with pytest.raises(ValueError, match="Magic Byte"):
        extract_text_from_pdf(fake_pdf)

def test_image_magic_bytes_validation():
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    fake_bytes = b"EXE_FILE_DATA_HERE"
    assert validate_image_magic_bytes(png_bytes) is True
    assert validate_image_magic_bytes(fake_bytes) is False

def test_ssrf_webhook_protection():
    # Private / Loopback IP blokları engellenmeli
    safe_localhost, _ = is_safe_webhook_url("http://127.0.0.1/webhook")
    safe_localname, _ = is_safe_webhook_url("http://localhost:8000/callback")
    safe_cloud_meta, _ = is_safe_webhook_url("http://169.254.169.254/latest/meta-data")
    safe_file_scheme, _ = is_safe_webhook_url("file:///etc/passwd")
    
    assert safe_localhost is False
    assert safe_localname is False
    assert safe_cloud_meta is False
    assert safe_file_scheme is False

def test_contextual_risk_engine_mitigators():
    historical_text = "CONFIDENTIAL REPORT: This report discusses a historical attack from 2021. All systems remediated. No systems affected currently."
    active_attack_text = "ACTIVE ATTACK: Massive data breach and ransomware attack detected! Servers are currently compromised! Urgent action required."

    hist_risk = analyze_risk(historical_text)
    active_risk = analyze_risk(active_attack_text)

    assert hist_risk["is_mitigated"] is True
    assert hist_risk["risk_level"] in ("Low", "Medium")
    assert "Tarihi" in hist_risk["incident_status"]

    assert active_risk["risk_level"] == "High"
    assert "Aktif" in active_risk["incident_status"]

def test_cv_document_intelligence():
    cv_text = """
    ÖZGEÇMİŞ / CURRICULUM VITAE
    Ahmet Yılmaz - Kıdemli Veri Mühendisi
    İş Deneyimi & Eğitim:
    - Apache Spark, PySpark, Python, SQL, Neo4j, Pandas, Docker, Git.
    - Büyük veri işleme ve grafik veritabanı mimarisi projeleri geliştirdi.
    """
    assert is_cv_document(cv_text) is True
    result = analyze_cv_document(cv_text)
    assert result["is_cv"] is True
    assert "Python" in result["detected_tech_stack"]
    assert "Spark" in result["detected_tech_stack"]
    assert "Veri Mühendisliği" in result["specialization"]

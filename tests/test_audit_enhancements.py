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
    assert hist_risk["risk_level"].upper() in ("LOW", "MEDIUM")
    assert "Tarihi" in hist_risk["incident_status"]

    assert active_risk["risk_level"].upper() in ("HIGH", "CRITICAL")
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


# ─────────────────────────────────────────────────────────────────
# P0 Yeni Testler — Bölüm 1 Doğrulama
# ─────────────────────────────────────────────────────────────────

def test_identity_card_classification():
    """Kimlik kartı dokümanı artık 'Literature & Arts' değil 'IDENTITY_CARD' olmalı."""
    from app.services.category_service import predict_category, get_category_label
    id_card_text = """
    TÜRKİYE CUMHURİYETİ KİMLİK KARTI
    Soyad / Surname: YILMAZ
    Ad / Given Name: AHMET
    Doğum Tarihi / Date of Birth: 01.01.1990
    Belge No / Document No: A12345678
    T.C. Kimlik No: 12345678901
    Geçerlilik / Validity: 01.01.2030
    """
    cat = predict_category(id_card_text)
    assert cat == "IDENTITY_CARD", f"Kimlik kartı IDENTITY_CARD olmalı, '{cat}' döndü"
    lbl = get_category_label(cat)
    assert "Kimlik" in lbl or "Pasaport" in lbl, f"Label kimlik içermeli: {lbl}"


def test_resume_classification():
    """CV / Özgeçmiş RESUME_CV olarak sınıflandırılmalı."""
    from app.services.category_service import predict_category
    cv_text = """
    ÖZGEÇMİŞ — CURRICULUM VITAE
    Professional Summary: 5 years experience in data engineering.
    Work Experience: Senior Data Engineer at TechCorp (2020-2025)
    Technical Skills: Python, Apache Spark, PostgreSQL, Docker
    Education: Boğaziçi Üniversitesi, Bilgisayar Mühendisliği
    """
    cat = predict_category(cv_text)
    assert cat == "RESUME_CV", f"CV RESUME_CV olmalı, '{cat}' döndü"


def test_multidimensional_risk_identity_card():
    """Kimlik kartı için gizlilik riski CRITICAL, güvenlik tehdidi LOW olmalı."""
    from app.services.risk_service import analyze_risk_multidimensional
    id_text = "T.C. Kimlik No: 12345678901, Ad: Ahmet Yılmaz, Doğum: 01.01.1990"
    pii = [{"type": "TCKN"}, {"type": "BIRTH_DATE"}, {"type": "FULL_NAME"}]
    result = analyze_risk_multidimensional(id_text, category="IDENTITY_CARD", pii_entities=pii)
    assert result["privacy_exposure"]["level"] in ("HIGH", "CRITICAL"), \
        f"ID kartı gizlilik riski yüksek olmalı: {result['privacy_exposure']}"
    assert result["security_threat"]["level"] in ("LOW", "MEDIUM"), \
        f"ID kartı güvenlik tehdidi düşük olmalı: {result['security_threat']}"


def test_kvkk_report_no_kritik_ihlal_language():
    """KVKK raporu artık 'Kritik KVKK İhlali' değil, doğru dil kullanmalı."""
    from app.services.ner_service import calculate_kvkk_report
    # Kritik PII varlıkları ile test
    entities = [{"type": "TCKN", "label": "TCKN", "text": "12345678901", "confidence_score": 0.98}]
    report = calculate_kvkk_report(entities)
    assert "Kritik KVKK İhlali" not in report["status"], \
        f"Eski 'Kritik KVKK İhlali' dili kullanılmamalı: {report['status']}"
    assert "kvkk_risk_label" in report, "kvkk_risk_label alanı eksik"
    assert report["total_entities"] == 1


def test_residual_scan_in_pipeline():
    """Routes pipeline artık redaction_verification dönmeli."""
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    payload = {"text": "TC Kimlik No: 12345678901, E-posta: test@example.com"}
    resp = c.post("/analyze-text", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "redaction_verification" in data, "redaction_verification eksik"
    rv = data["redaction_verification"]
    assert "detected" in rv
    assert "masked" in rv
    assert "residual" in rv
    assert "status" in rv
    assert rv["status"] in ("VERIFIED", "INCOMPLETE")


def test_new_pii_social_profile():
    """Sosyal profil linkleri SOCIAL_PROFILE olarak tespit edilmeli."""
    from app.services.ner_service import detect_pii_entities
    text = "Profilim: linkedin.com/in/ahmetyilmaz veya github.com/ahmet123 adresinden ulaşabilirsiniz."
    entities = detect_pii_entities(text)
    types = [e["type"] for e in entities]
    assert "SOCIAL_PROFILE" in types, f"linkedin/github SOCIAL_PROFILE olmalı. Bulunanlar: {types}"


# ─────────────────────────────────────────────────────────────────
# Bölüm 2 (P1) Yeni Testler — MRZ, Structured Data, Visual PII, OCR
# ─────────────────────────────────────────────────────────────────

def test_mrz_parsing_td1_identity_card():
    """TD1 3-satırlı Kimlik Kartı MRZ çözümleme ve checksum doğrulaması."""
    from app.services.mrz_service import parse_mrz, calculate_mrz_check_digit
    
    # ICAO Doc 9303 TD1 Örneği (T.C. Kimlik Kartı MRZ)
    sample_id_text = """
    TÜRKİYE CUMHURİYETİ KİMLİK KARTI
    Soyadı: YILMAZ Adı: AHMET
    I<TURA12B345674<<<<<<<<<<<<<<<
    9001018M3001014TUR123456789012
    YILMAZ<<AHMET<<<<<<<<<<<<<<<<<
    """
    mrz = parse_mrz(sample_id_text)
    assert mrz is not None, "MRZ tespit edilmeli"
    assert mrz["format"] == "TD1"
    assert mrz["document_type"] == "IDENTITY_CARD"
    assert mrz["document_number"] == "A12B34567"
    assert mrz["surname"] == "YILMAZ"
    assert mrz["given_names"] == "AHMET"
    assert mrz["birth_date"] == "1990-01-01"
    assert mrz["expiry_date"] == "2030-01-01"
    assert mrz["sex"] == "M"
    assert mrz["nationality"] == "TUR"
    assert mrz["tckn"] == "12345678901"


def test_mrz_parsing_td3_passport():
    """TD3 2-satırlı Pasaport MRZ çözümlemesi."""
    from app.services.mrz_service import parse_mrz
    
    passport_text = """
    PASAPORT / PASSPORT
    P<TURYILMAZ<<AHMET<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    U123456780TUR9001018M300101412345678901<<<<<4
    """
    mrz = parse_mrz(passport_text)
    assert mrz is not None, "Pasaport MRZ tespit edilmeli"
    assert mrz["format"] == "TD3"
    assert mrz["document_type"] == "PASSPORT"
    assert mrz["document_number"] == "U12345678"
    assert mrz["surname"] == "YILMAZ"
    assert mrz["given_names"] == "AHMET"
    assert mrz["birth_date"] == "1990-01-01"
    assert mrz["expiry_date"] == "2030-01-01"


def test_structured_document_extraction_identity():
    """Kimlik kartı metninden yapılandırılmış alan çıkarımı."""
    from app.services.document_extractor import extract_structured_document_data
    
    id_text = """
    TÜRKİYE CUMHURİYETİ KİMLİK KARTI
    T.C. Kimlik No: 12345678901
    Soyadı / Surname: YILMAZ
    Adı / Given Name: MEHMET ALİ
    Doğum Tarihi / Date of Birth: 15.08.1992
    Belge No / Document No: A12B34567
    Son Geçerlilik / Valid Until: 15.08.2032
    Cinsiyeti / Sex: Erkek / M
    Uyruğu / Nationality: T.C.
    Anne Adı: FATMA  Baba Adı: HASAN
    """
    result = extract_structured_document_data(id_text, category="IDENTITY_CARD")
    assert result["document_type"] == "IDENTITY_CARD"
    fields = result["fields"]
    assert fields.get("tckn") == "12345678901"
    assert fields.get("surname") == "YILMAZ"
    assert "MEHMET" in fields.get("given_name", "")
    assert fields.get("birth_date") == "15.08.1992"
    assert fields.get("document_no") == "A12B34567"
    assert fields.get("valid_until") == "15.08.2032"
    assert "Erkek" in fields.get("gender", "")
    assert fields.get("mother_name") == "FATMA"
    assert fields.get("father_name") == "HASAN"


def test_visual_pii_detection():
    """Görsel PII unsurlarının (fotoğraf, imza, çip, barkod) tespiti."""
    from app.services.document_extractor import detect_visual_pii_elements
    
    doc_text = """
    SÜRÜCÜ BELGESİ / DRIVING LICENCE
    Biyometrik fotoğraf alanı mevcuttur.
    Sahibinin imzası: [İMZA]
    Elektronik çip ve hologram güvenlik şeridi bulunur.
    """
    visual_items = detect_visual_pii_elements(doc_text)
    types = [item["type"] for item in visual_items]
    assert "BIOMETRIC_PHOTO" in types
    assert "HANDWRITTEN_SIGNATURE" in types
    assert "SMART_CHIP_HOLOGRAM" in types


def test_document_type_aware_keywords():
    """Kimlik kartı için 'Soyad', 'Surname', 'Turkey' gibi şablon kelimeler filtrelenmeli."""
    from app.services.keyword_service import extract_keywords
    
    id_text = """
    TÜRKİYE CUMHURİYETİ KİMLİK KARTI
    Soyad / Surname: KARADENİZ
    Ad / Given Name: VOLKAN
    Doğum Tarihi / Date of Birth: 01.01.1990
    Belge No / Document No: A12B34567
    Biyometrik Kriptografi ve Yapay Zeka Sertifikasyonu
    """
    keywords = extract_keywords(id_text, category="IDENTITY_CARD", top_n=5)
    lower_kws = [k.lower() for k in keywords]
    assert "soyad" not in lower_kws
    assert "surname" not in lower_kws
    assert "given" not in lower_kws
    assert "türkiye" not in lower_kws
    assert "kartı" not in lower_kws


def test_image_preprocessing_pipeline():
    """Görsel ön işleme hattının (upscaling, contrast, grayscale) doğrulanması."""
    from app.services.ocr_service import preprocess_image_for_ocr
    from PIL import Image
    import io
    
    # Küçük bir test görseli oluştur (200x100)
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    
    processed_img, metadata = preprocess_image_for_ocr(img_bytes)
    assert metadata["preprocessed"] is True
    assert metadata["scale_factor"] > 1.0  # Küçük görsel büyütülmeli
    assert processed_img.mode == "L"       # Grayscale olmalı
    assert processed_img.size[0] > 200    # Genişlik artırılmış olmalı


def test_end_to_end_pipeline_structured_response():
    """Routes pipeline'ının structured_data, visual_pii ve mrz_data dönmesini test et."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    c = TestClient(app)
    sample_id = """
    TÜRKİYE CUMHURİYETİ KİMLİK KARTI
    T.C. Kimlik No: 12345678901
    Soyadı: KAYA
    Adı: CAN
    Doğum Tarihi: 10.10.1995
    Belge No: B98A76543
    Geçerlilik: 10.10.2035
    I<TURB98A765430<<<<<<<<<<<<<<<
    9510105M3510108TUR123456789010
    KAYA<<CAN<<<<<<<<<<<<<<<<<<<<<
    """
    resp = c.post("/analyze-text", json={"text": sample_id})
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["category"] == "IDENTITY_CARD"
    assert "structured_data" in data and data["structured_data"] is not None
    assert data["structured_data"].get("surname") == "KAYA"
    assert data["structured_data"].get("tckn") == "12345678901"
    assert "mrz_data" in data and data["mrz_data"] is not None
    assert data["mrz_data"]["document_number"] == "B98A76543"
    assert "visual_pii" in data
    assert len(data["visual_pii"]) > 0


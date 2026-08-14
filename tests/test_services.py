import pytest
import os
from unittest.mock import patch, MagicMock
from app.utils.text_cleaner import clean_text
from app.utils.language_detector import detect_language, get_language_label
from app.services.risk_service import analyze_risk
from app.services.keyword_service import extract_keywords
from app.services.category_service import predict_category
from app.services.summary_service import generate_summary
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import is_llm_available, generate_llm_summary

def test_text_cleaner():
    raw = "  Bu   bir \n\n test   metnidir.   \t "
    cleaned = clean_text(raw)
    assert cleaned == "Bu bir test metnidir."

def test_language_detector_tr():
    tr_text = "Şirketimizin üçüncü çeyrek finansal sonuçları ve kâr marjı açıklandı."
    assert detect_language(tr_text) == "tr"
    assert get_language_label("tr") == "Türkçe"

def test_language_detector_en():
    en_text = "The quarterly financial report was published with record net profits."
    assert detect_language(en_text) == "en"
    assert get_language_label("en") == "English"

def test_risk_service_empty():
    res = analyze_risk("")
    assert res["risk_score"] == 0
    assert res["risk_level"] == "Low"

def test_risk_service_high_risk_en():
    text = "Critical security breach detected! A zero-day exploit and ransomware caused a massive data leak."
    res = analyze_risk(text)
    assert res["risk_score"] > 5
    assert res["risk_level"] in ["Medium", "High"]

def test_risk_service_high_risk_tr():
    text = "Sistemlerimizde kritik bir sıfır gün güvenlik açığı tespit edildi ve fidye yazılımı nedeniyle veri sızıntısı yaşandı."
    res = analyze_risk(text)
    assert res["risk_score"] > 5
    assert res["risk_level"] in ["Medium", "High"]

def test_risk_service_word_boundary():
    text = "The doctor noted a general case without any true attack."
    res = analyze_risk(text)
    assert isinstance(res["risk_score"], int)

def test_keyword_service_en():
    text = "Artificial intelligence and machine learning models are transforming automated document analysis."
    keywords = extract_keywords(text, top_n=3, language="en")
    assert isinstance(keywords, list)
    assert len(keywords) > 0

def test_keyword_service_tr():
    text = "Yapay zekâ ve derin öğrenme algoritmaları ile otomatik doküman analitiği geliştirilmektedir."
    keywords = extract_keywords(text, top_n=3, language="tr")
    assert isinstance(keywords, list)
    assert len(keywords) > 0

def test_keyword_service_empty():
    assert extract_keywords("") == []

def test_category_service_en():
    text = "The company reported record quarterly revenue and high profit margins on stock investments."
    cat = predict_category(text)
    assert cat == "Finance"

def test_category_service_tr():
    text = "Hastanedeki doktorlar ve cerrahi ekipler yeni bir klinik tedavi ve aşı protokolü geliştirdi."
    cat = predict_category(text)
    assert cat == "Healthcare"

def test_category_service_tr_cyber():
    text = "Siber saldırganlar güvenlik açığından yararlanarak sisteme sızma girişimi yaptı ve zafiyet oluşturdu."
    cat = predict_category(text)
    assert cat == "Cyber Security"

def test_summary_service_short_text_en():
    text = "I went to school today."
    summary = generate_summary(text, language="en")
    assert isinstance(summary, str)
    assert len(summary) > 0
    # Özet ham cümlenin aynısı olmamalı (Groq veya yerel sentez ile özetlenmeli)
    assert summary.strip() != text.strip()

def test_summary_service_short_text_tr():
    text = "Bildiğiniz üzere, bugün üniversitede yapay zeka ve derin öğrenme modelleri üzerine kapsamlı bir ders işlendi."
    summary = generate_summary(text, language="tr")
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "Bildiğiniz üzere" not in summary

def test_summary_service_multi_sentence():
    text = (
        "Artificial intelligence is rapidly advancing across various sectors. "
        "Healthcare systems are adopting machine learning algorithms for diagnostics. "
        "Financial institutions use AI models for automated fraud detection. "
        "Overall, these intelligent systems improve efficiency and accuracy."
    )
    summary = generate_summary(text, max_sentences=2)
    assert isinstance(summary, str)
    assert len(summary) > 0

def test_llm_service_no_key():
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
        assert is_llm_available() is False
        assert generate_llm_summary("Some sample text") is None

def test_llm_service_mock_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "This is a freshly generated abstractive summary from Groq."}}
        ]
    }
    
    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test123", "LLM_ENABLED": "true"}):
        with patch("httpx.Client.post", return_value=mock_response):
            summary = generate_llm_summary("Original document text here.", language="en")
            assert summary == "This is a freshly generated abstractive summary from Groq."

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

def test_translate_text_mock():
    from app.services.llm_service import translate_text
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Bu bir çeviri örneğidir."}}
        ]
    }
    
    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test123", "LLM_ENABLED": "true"}):
        with patch("httpx.Client.post", return_value=mock_response):
            translated = translate_text("This is a translation sample.", target_language="tr")
            assert translated == "Bu bir çeviri örneğidir."


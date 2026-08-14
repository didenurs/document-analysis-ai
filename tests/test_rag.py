import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.rag_service import chunk_document, retrieve_relevant_chunks, generate_rag_answer

client = TestClient(app)

SAMPLE_DOC = """
GİZLİ OLAY RAPORU: ACİL SALDIRI MÜDAHALESİ GEREKLİDİR.
Saat 02:00 sularında dahili izleme sistemlerimiz, merkezi kurumsal ağımızın veritabanı güvenlik duvarında kritik bir arıza tespit etti.
Saldırganlar sıfır gün güvenlik açığını istismar ederek 50.000 müşterinin finansal verilerine erişti.
Olay müdahale ekibi derhal sunucuları izole etti ve sistem yöneticilerine tüm şifreleri sıfırlama talimatı verdi.
Güvenlik açığı için yama 1 saat içinde yayınlanacaktır.
"""

def test_chunk_document_empty():
    assert chunk_document("") == []
    assert chunk_document("   ") == []

def test_chunk_document_single_and_multi():
    short_text = "Bu kısa bir metindir."
    chunks = chunk_document(short_text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    long_text = "Cümle 1. " * 30
    chunks = chunk_document(long_text, chunk_size=100, overlap=20)
    assert len(chunks) > 1

def test_retrieve_relevant_chunks():
    chunks = [
        "Finansal büyüme ve kâr oranları bu çeyrekte %20 arttı.",
        "Siber güvenlik ihlali saat 02:00'de veritabanı duvarında gerçekleşti.",
        "Yeni çalışan oryantasyon programı önümüzdeki hafta başlayacaktır."
    ]
    
    query = "Siber güvenlik saldırısı ne zaman oldu?"
    relevant = retrieve_relevant_chunks(chunks, query, top_k=1)
    assert len(relevant) == 1
    assert "Siber güvenlik" in relevant[0]["text"]

def test_generate_rag_answer_fallback_no_key():
    with patch.dict(os.environ, {"GROQ_API_KEY": "", "LLM_ENABLED": "false"}):
        result = generate_rag_answer(SAMPLE_DOC, "Saldırı ne zaman oldu?", language="tr")
        assert "answer" in result
        assert len(result["sources"]) > 0
        assert "02:00" in result["answer"] or "02:00" in result["sources"][0]

def test_generate_rag_answer_mock_llm():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Saldırı saat 02:00'de veritabanı güvenlik duvarında meydana gelmiştir."}}
        ]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test123", "LLM_ENABLED": "true"}):
        with patch("httpx.Client.post", return_value=mock_response):
            result = generate_rag_answer(SAMPLE_DOC, "Saldırı saat kaçta oldu?", language="tr")
            assert "02:00" in result["answer"]
            assert result["confidence"] > 0.5
            assert len(result["sources"]) > 0

def test_chat_document_endpoint_success():
    mock_rag_result = {
        "answer": "Saldırıda 50.000 müşterinin finansal verileri etkilenmiştir.",
        "sources": ["Saldırganlar 50.000 müşterinin verisine erişti."],
        "confidence": 0.95,
        "language": "tr"
    }

    with patch("app.api.routes.generate_rag_answer", return_value=mock_rag_result):
        payload = {
            "document_text": SAMPLE_DOC,
            "question": "Kaç müşteri etkilendi?",
            "history": [],
            "language": "tr"
        }
        response = client.post("/chat-document", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "50.000" in data["answer"]
        assert len(data["sources"]) > 0
        assert data["confidence"] == 0.95


def test_chat_document_endpoint_empty_inputs():
    res1 = client.post("/chat-document", json={"document_text": "", "question": "test"})
    assert res1.status_code == 400

    res2 = client.post("/chat-document", json={"document_text": "sample text", "question": "   "})
    assert res2.status_code == 400

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.compare_service import compare_two_documents
from app.services.batch_service import aggregate_batch_results
from app.services.export_service import generate_json_bytes, generate_csv_bytes, generate_html_report
from app.api.routes import process_text_pipeline

client = TestClient(app)

def test_compare_service_diff():
    doc1 = "Sözleşme bedeli 50.000 TL olarak belirlenmiştir. İletişim: destek@test.com"
    doc2 = "Sözleşme bedeli 85.000 TL olarak belirlenmiştir. Ayrıca KVKK kapsamında TCKN 12345678901 eklenmiştir."
    
    res = compare_two_documents(doc1, doc2, "Eski", "Yeni", language="tr")
    assert res.similarity_percentage > 0
    assert isinstance(res.doc1_risk_score, int)
    assert isinstance(res.doc2_risk_score, int)
    assert res.pii_diff_count >= 0
    assert len(res.summary_comparison) > 0

def test_batch_service_aggregation():
    resp1 = process_text_pipeline("Acil siber güvenlik ihlali ve veri sızıntısı tespit edildi.")
    resp2 = process_text_pipeline("Ahmet Yılmaz TCKN 10000000146 telefon 0532 123 45 67")
    
    batch_res = aggregate_batch_results([
        ("doc1.txt", resp1),
        ("doc2.txt", resp2)
    ])
    
    assert batch_res.total_documents == 2
    assert batch_res.global_risk_score > 0
    assert len(batch_res.documents) == 2
    assert batch_res.global_kvkk_report.total_entities >= 1

def test_export_service():
    sample_data = {
        "summary": "Test Özeti",
        "category": "Teknoloji",
        "risk_level": "Medium",
        "risk_score": 45,
        "language": "tr",
        "keywords": ["test", "analiz"],
        "kvkk_report": {"status": "GÜVENLİ", "total_entities": 0, "breakdown": {}}
    }
    
    j_bytes = generate_json_bytes(sample_data)
    assert "Test Özeti".encode('utf-8') in j_bytes
    
    c_bytes = generate_csv_bytes(sample_data)
    assert "Test Özeti".encode('utf-8') in c_bytes
    
    html = generate_html_report(sample_data)
    assert "Doc Analysis AI" in html
    assert "Test Özeti" in html
    assert "print-btn" not in html
    assert "PDF Olarak Kaydet" not in html

def test_api_compare_documents():
    payload = {
        "doc1_text": "Metin 1 içeriği burada yer alıyor.",
        "doc2_text": "Metin 2 içeriği revize edilmiş haliyle burada.",
        "doc1_title": "D1",
        "doc2_title": "D2"
    }
    response = client.post("/compare-documents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "similarity_percentage" in data
    assert "summary_comparison" in data

def test_api_analyze_batch():
    files = [
        ("files", ("test1.txt", b"Siber guvenlik ihlali acil mudahale gerektirir.", "text/plain")),
        ("files", ("test2.txt", b"Sayin Ahmet Yilmaz TCKN 12345678901", "text/plain"))
    ]
    response = client.post("/analyze-batch", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 2
    assert "global_risk_score" in data
    assert len(data["documents"]) == 2

def test_api_export_endpoints():
    payload = {
        "analysis_data": {
            "summary": "Rapor Özeti",
            "category": "Finance",
            "risk_level": "Low",
            "risk_score": 10,
            "masked_text": "Sayın A*** Y***** TCKN 100*****46"
        },
        "export_format": "json"
    }
    
    resp_json = client.post("/export/json", json=payload)
    assert resp_json.status_code == 200
    assert resp_json.headers["content-type"].startswith("application/json")

    resp_csv = client.post("/export/csv", json=payload)
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]

    resp_html = client.post("/export/html", json=payload)
    assert resp_html.status_code == 200
    assert "text/html" in resp_html.headers["content-type"]
    assert "print-btn" not in resp_html.text

    resp_pdf = client.post("/export/pdf", json=payload)
    assert resp_pdf.status_code == 200
    assert "application/pdf" in resp_pdf.headers["content-type"]
    assert len(resp_pdf.content) > 0

    resp_masked_pdf = client.post("/export/masked-pdf", json=payload)
    assert resp_masked_pdf.status_code == 200
    assert "application/pdf" in resp_masked_pdf.headers["content-type"]
    assert "maskelenmis_dokuman.pdf" in resp_masked_pdf.headers.get("content-disposition", "")
    assert len(resp_masked_pdf.content) > 0


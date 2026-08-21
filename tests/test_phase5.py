import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.anomaly_service import detect_document_anomalies
from app.services.recommendation_service import generate_action_recommendations
from app.services.metrics_service import record_analysis_metrics, get_system_metrics
from app.services.webhook_service import dispatch_webhook_event
from app.models.schemas import KVKKReport

client = TestClient(app)

def test_anomaly_detection_clean():
    res = detect_document_anomalies("Bu standart ve güvenli bir doküman metnidir.", category="General")
    assert not res.has_anomaly
    assert res.anomaly_score == 0

def test_anomaly_detection_suspicious():
    text = "ACİL HAVALE: Kimseye bahsetmeyin ve denetimden saklayın. Resmi kayıtlara geçirmeyin."
    res = detect_document_anomalies(text, category="Finance")
    assert res.has_anomaly
    assert res.anomaly_score >= 30
    assert len(res.anomaly_flags) > 0

def test_recommendations_generator():
    kvkk = KVKKReport(status="HASSAS VERİ İÇERİYOR", risk_level="High", total_entities=6, breakdown={"TCKN": 6})
    recs = generate_action_recommendations(
        category="Finance",
        risk_level="High",
        risk_score=80,
        kvkk_report=kvkk
    )
    assert len(recs) >= 2
    high_priority = [r for r in recs if r.priority == "High"]
    assert len(high_priority) >= 1

def test_metrics_service():
    record_analysis_metrics(category="Cyber Security", risk_score=75, pii_count=2)
    metrics = get_system_metrics()
    assert metrics.total_processed >= 1
    assert metrics.total_pii_masked >= 2
    assert "HEALTHY" in metrics.system_status

import asyncio

def test_webhook_dispatch_invalid():
    res = asyncio.run(dispatch_webhook_event("invalid-url", "test", {}))
    assert not res["success"]
    assert "Geçersiz" in res["message"]

def test_api_metrics_endpoint():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_processed" in data
    assert "avg_risk_score" in data

def test_api_webhook_test_endpoint():
    payload = {"webhook_url": "https://httpbin.org/post", "event_type": "risk.critical"}
    resp = client.post("/webhooks/test", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data

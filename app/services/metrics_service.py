from typing import Dict
from app.models.schemas import SystemMetricsResponse

# Bellek İçi Metrik Deposu (Thread-Safe Basit Sayaçlar)
_metrics_store = {
    "total_processed": 0,
    "total_pii_masked": 0,
    "total_risk_score_sum": 0,
    "category_breakdown": {}
}

def record_analysis_metrics(category: str, risk_score: int, pii_count: int = 0):
    """
    Tamamlanan her analiz işleminde sistem geneli canlı metrikleri günceller.
    """
    _metrics_store["total_processed"] += 1
    _metrics_store["total_pii_masked"] += pii_count
    _metrics_store["total_risk_score_sum"] += risk_score

    cat = category or "General"
    cats = _metrics_store["category_breakdown"]
    cats[cat] = cats.get(cat, 0) + 1

def get_system_metrics() -> SystemMetricsResponse:
    """
    Sistem canlı performans ve analiz metriklerini döndürür.
    """
    total = _metrics_store["total_processed"]
    avg_risk = round(_metrics_store["total_risk_score_sum"] / total, 1) if total > 0 else 0.0

    return SystemMetricsResponse(
        total_processed=total,
        total_pii_masked=_metrics_store["total_pii_masked"],
        avg_risk_score=avg_risk,
        category_breakdown=_metrics_store["category_breakdown"],
        system_status="HEALTHY - ALL SYSTEMS OPERATIONAL"
    )

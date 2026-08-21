from typing import List, Dict, Any, Tuple
from app.models.schemas import BatchAnalysisItem, BatchAnalysisResponse, KVKKReport, AnalysisResponse
from app.services.summary_service import generate_summary
from app.utils.language_detector import detect_language

def aggregate_batch_results(
    processed_items: List[Tuple[str, AnalysisResponse]]
) -> BatchAnalysisResponse:
    """
    İşlenmiş doküman sonuçlarını alarak toplu analiz özetini (global risk, global KVKK raporu,
    birleşik özet) hesaplar.
    """
    if not processed_items:
        empty_kvkk = KVKKReport(
            status="GÜVENLİ",
            risk_level="DÜŞÜK",
            total_entities=0,
            breakdown={}
        )
        return BatchAnalysisResponse(
            total_documents=0,
            overall_summary="İşlenecek doküman bulunamadı.",
            global_risk_level="Low",
            global_risk_score=0,
            global_kvkk_report=empty_kvkk,
            documents=[]
        )

    batch_docs: List[BatchAnalysisItem] = []
    combined_summaries: List[str] = []
    max_risk_score = 0
    total_pii_count = 0
    global_breakdown: Dict[str, int] = {}
    detected_langs: List[str] = []

    for filename, resp in processed_items:
        batch_docs.append(
            BatchAnalysisItem(
                filename=filename,
                extraction_method=resp.extraction_method or "text",
                page_count=resp.page_count,
                analysis=resp
            )
        )

        if resp.summary:
            combined_summaries.append(f"[{filename}]: {resp.summary}")

        if resp.risk_score > max_risk_score:
            max_risk_score = resp.risk_score

        if resp.language:
            detected_langs.append(resp.language)

        if resp.kvkk_report:
            total_pii_count += resp.kvkk_report.total_entities
            for entity_type, count in resp.kvkk_report.breakdown.items():
                global_breakdown[entity_type] = global_breakdown.get(entity_type, 0) + count

    # Genel Risk Seviyesi Belirleme
    if max_risk_score >= 70:
        global_risk_level = "High"
    elif max_risk_score >= 35:
        global_risk_level = "Medium"
    else:
        global_risk_level = "Low"

    # KVKK Genel Statü
    if total_pii_count == 0:
        kvkk_status = "GÜVENLİ"
        kvkk_risk = "DÜŞÜK"
    elif total_pii_count <= 5:
        kvkk_status = "HASSAS VERİ İÇERİYOR"
        kvkk_risk = "ORTA"
    else:
        kvkk_status = "YÜKSEK GİZLİLİK RİSKİ"
        kvkk_risk = "YÜKSEK"

    global_kvkk = KVKKReport(
        status=kvkk_status,
        risk_level=kvkk_risk,
        total_entities=total_pii_count,
        breakdown=global_breakdown
    )

    # Genel Birleşik Özet Üretimi
    dominant_lang = "tr" if detected_langs.count("tr") >= len(detected_langs) / 2 else "en"
    if combined_summaries:
        corpus_for_summary = "\n\n".join(combined_summaries)
        if len(corpus_for_summary) > 2000:
            corpus_for_summary = corpus_for_summary[:2000] + "..."
        overall_summary = generate_summary(corpus_for_summary, language=dominant_lang)
    else:
        overall_summary = "Toplu doküman analizi tamamlandı."

    return BatchAnalysisResponse(
        total_documents=len(batch_docs),
        overall_summary=overall_summary,
        global_risk_level=global_risk_level,
        global_risk_score=max_risk_score,
        global_kvkk_report=global_kvkk,
        documents=batch_docs
    )

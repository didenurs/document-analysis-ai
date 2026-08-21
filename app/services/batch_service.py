import os
import httpx
from typing import List, Dict, Any, Tuple
from app.models.schemas import BatchAnalysisItem, BatchAnalysisResponse, KVKKReport, AnalysisResponse
from app.services.summary_service import generate_summary
from app.services.llm_service import is_llm_available, GROQ_API_URL
from app.utils.language_detector import detect_language

def _generate_batch_executive_summary(
    processed_items: List[Tuple[str, AnalysisResponse]],
    dominant_lang: str = "tr"
) -> str:
    """Toplu analiz edilen tüm dokümanlar için 2-3 cümlelik temiz birleşik özet üretir."""
    if not processed_items:
        return "Toplu doküman analizi tamamlandı."

    filenames = [fname for fname, _ in processed_items]
    categories = sorted(list({resp.category for _, resp in processed_items if resp.category}))
    doc_summaries = [f"- {fname}: {resp.summary}" for fname, resp in processed_items if resp.summary]

    # 1. Groq LLM Sentezleyici
    if is_llm_available() and doc_summaries:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        selected_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        lang_name = "Türkçe" if dominant_lang == "tr" else "English"
        
        system_prompt = (
            f"You are an executive AI report synthesizer. "
            f"Synthesize a brief, high-level 2-3 sentence overall summary in {lang_name} for a batch of {len(processed_items)} documents. "
            f"Describe the main topics and document categories analyzed as a unified whole. "
            f"Do NOT list document filenames or copy raw bullets line-by-line. Output ONLY the clean 2-3 sentence executive summary in {lang_name}."
        )
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Individual document summaries:\n" + "\n".join(doc_summaries[:5])}
            ],
            "temperature": 0.2,
            "max_tokens": 250
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(GROQ_API_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    summary = res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if summary:
                        return summary.strip('"').strip("'").strip()
        except Exception:
            pass

    # 2. Akıllı Yerel Fallback Sentezleyici
    cats_str = ", ".join(categories) if categories else ("Genel" if dominant_lang == "tr" else "General")
    files_str = ", ".join(filenames[:3])
    if len(filenames) > 3:
        files_str += f" (+{len(filenames)-3} dosya)"

    if dominant_lang == "tr":
        return f"Toplu analiz kapsamında {len(processed_items)} adet doküman ({cats_str} kategorilerinde) başarıyla incelenmiştir. İncelenen dosyalar ({files_str}) genel içerik, güvenlik durumu ve veri gizliliği standartları açısından değerlendirilmiştir."
    else:
        return f"A total of {len(processed_items)} documents across categories ({cats_str}) were successfully analyzed ({files_str}) for content, security risk, and data privacy."

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
    overall_summary = _generate_batch_executive_summary(processed_items, dominant_lang=dominant_lang)

    return BatchAnalysisResponse(
        total_documents=len(batch_docs),
        overall_summary=overall_summary,
        global_risk_level=global_risk_level,
        global_risk_score=max_risk_score,
        global_kvkk_report=global_kvkk,
        documents=batch_docs
    )

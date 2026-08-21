import re
from typing import List, Set, Dict, Any
from app.models.schemas import DocumentCompareResponse
from app.services.category_service import predict_category
from app.services.risk_service import analyze_risk
from app.services.ner_service import mask_pii_text
from app.utils.language_detector import detect_language

def compute_jaccard_similarity(text1: str, text2: str) -> float:
    """İki metin arasındaki kelime kümesi Jaccard benzerlik oranını hesaplar (0.0 - 1.0)."""
    words1: Set[str] = set(re.findall(r'\w+', text1.lower()))
    words2: Set[str] = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
        
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def extract_key_sentences(text: str) -> List[str]:
    """Metinden anlamlı ve bağımsız cümleleri ayrıştırır."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 15]

def compare_two_documents(
    doc1_text: str, 
    doc2_text: str, 
    doc1_title: str = "Doküman 1", 
    doc2_title: str = "Doküman 2",
    language: str = None
) -> DocumentCompareResponse:
    """
    İki dokümanı karşılaştırarak benzerlik skorunu, risk değişimini, kategori farklarını,
    eklenen/çıkarılan kritik ifadeleri ve KVKK veri farklarını çıkarır.
    """
    cleaned1 = doc1_text.strip()
    cleaned2 = doc2_text.strip()
    
    if not cleaned1 or not cleaned2:
        return DocumentCompareResponse(
            similarity_score=0.0,
            similarity_percentage=0,
            risk_delta=0,
            risk_status="Geçersiz metin",
            added_keypoints=[],
            removed_keypoints=[],
            doc1_category="Belirsiz",
            doc2_category="Belirsiz",
            doc1_risk_score=0,
            doc2_risk_score=0,
            pii_diff_count=0,
            summary_comparison="Karşılaştırma yapmak için her iki doküman da metin içermelidir."
        )

    # 1. Benzerlik Skoru
    sim_score = compute_jaccard_similarity(cleaned1, cleaned2)
    sim_pct = int(round(sim_score * 100))

    # 2. Kategoriler
    cat1 = predict_category(cleaned1)
    cat2 = predict_category(cleaned2)

    # 3. Risk Değerlendirmesi
    risk_data1 = analyze_risk(cleaned1)
    risk_data2 = analyze_risk(cleaned2)
    
    risk1 = risk_data1["risk_score"]
    risk2 = risk_data2["risk_score"]
    risk_delta = risk2 - risk1

    if risk_delta > 0:
        risk_status = f"Risk Yükseldi (+%{risk_delta})"
    elif risk_delta < 0:
        risk_status = f"Risk Düştü (%{risk_delta})"
    else:
        risk_status = "Risk Seviyesi Aynı"

    # 4. PII (KVKK) Farkı
    _, _, kvkk1 = mask_pii_text(cleaned1)
    _, _, kvkk2 = mask_pii_text(cleaned2)
    pii_diff_count = kvkk2["total_entities"] - kvkk1["total_entities"]

    # 5. Cümle / Madde Farkları
    sentences1 = set(extract_key_sentences(cleaned1))
    sentences2 = set(extract_key_sentences(cleaned2))

    removed_sentences = list(sentences1 - sentences2)[:5]
    added_sentences = list(sentences2 - sentences1)[:5]

    # 6. Karşılaştırma Özeti Metni
    lang = language or detect_language(cleaned1 + " " + cleaned2)
    if lang == "tr":
        summary_comp = (
            f"'{doc1_title}' ve '{doc2_title}' dokümanları %{sim_pct} oranında benzerlik göstermektedir. "
            f"Risk skoru {risk1} seviyesinden {risk2} seviyesine ({risk_status.lower()}) değişmiştir. "
            f"Doküman 1 kategorisi '{cat1}', Doküman 2 kategorisi ise '{cat2}' olarak tespit edilmiştir. "
            f"Hassas veri (PII) farkı: {pii_diff_count:+d} varlık."
        )
    else:
        summary_comp = (
            f"'{doc1_title}' and '{doc2_title}' show {sim_pct}% content similarity. "
            f"Risk score shifted from {risk1} to {risk2} ({risk_status}). "
            f"Categories: '{cat1}' vs '{cat2}'. PII entity count difference: {pii_diff_count:+d}."
        )

    return DocumentCompareResponse(
        similarity_score=round(sim_score, 4),
        similarity_percentage=sim_pct,
        risk_delta=risk_delta,
        risk_status=risk_status,
        added_keypoints=added_sentences,
        removed_keypoints=removed_sentences,
        doc1_category=cat1,
        doc2_category=cat2,
        doc1_risk_score=risk1,
        doc2_risk_score=risk2,
        pii_diff_count=pii_diff_count,
        summary_comparison=summary_comp
    )

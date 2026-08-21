import re
from typing import List
from app.models.schemas import AnomalyReport

SUSPICIOUS_PHRASES = [
    # Türkçe Şüpheli / Manipülatif İfadeler
    "kimseye bahsetmeyin", "denetimden saklayın", "gizli hesaba", "resmi kayıtlara geçirmeyin",
    "acil havale", "faturalandırmadan", "sözlü talimat", "kayıtsız ödeme", "yetkisiz erişim",
    
    # İngilizce Şüpheli İfadeler
    "off the record", "do not audit", "unauthorized wire", "bypass approval",
    "do not log", "urgent wire transfer", "confidential bypass", "untraceable payment"
]

def detect_document_anomalies(text: str, category: str = "General") -> AnomalyReport:
    """
    Doküman metnini tarayarak anomali göstergelerini, sahtecilik/manipülasyon şüphelerini
    ve OCR karakter bozulmalarını analiz eder.
    """
    flags: List[str] = []
    anomaly_score = 0
    lower_text = text.lower()

    # 1. Manipülatif / Şüpheli Dil Tespiti
    found_phrases = [p for p in SUSPICIOUS_PHRASES if p in lower_text]
    if found_phrases:
        anomaly_score += len(found_phrases) * 25
        flags.append(f"Şüpheli / Manipülatif İfadeler Tespiti ({', '.join(found_phrases)})")

    # 2. OCR Karakter Bozulması / Gürültü Tespiti
    non_ascii_weird = len(re.findall(r'[^\w\s\.,!\?\-:\(\)\'\"]', text))
    total_len = max(len(text), 1)
    noise_ratio = non_ascii_weird / total_len
    if noise_ratio > 0.12:
        anomaly_score += 20
        flags.append("Yüksek OCR Gürültüsü / Karakter Bozulması Tespiti")

    # 3. Finansal Tutarsızlık Şüphesi (Finans / Fatura kategorilerinde)
    if category.lower() in ["finance", "finans", "fatura"]:
        amounts = [float(a.replace(',', '.')) for a in re.findall(r'\b\d+(?:[\.,]\d{2})?\b', text) if len(a) > 2]
        if len(amounts) >= 3:
            max_amount = max(amounts)
            if max_amount > 1000000 and min(amounts) < 10:
                anomaly_score += 15
                flags.append("Olağandışı Finansal Tutar Sapması")

    # 4. Aşırı Büyük Harf Kullanımı (Şüpheli Vurgu)
    words = text.split()
    uppercase_words = [w for w in words if w.isupper() and len(w) > 3]
    if len(words) > 10 and (len(uppercase_words) / len(words)) > 0.4:
        anomaly_score += 15
        flags.append("Aşırı Büyük Harf (Baskı/Manipülasyon) Kullanımı")

    anomaly_score = min(anomaly_score, 100)
    has_anomaly = anomaly_score >= 30

    if not flags:
        details = "Dokümanda herhangi bir anomali veya manipülasyon şüphesi tespit edilmedi."
    else:
        details = f"Dokümanda {len(flags)} adet anomali göstergesi tespit edildi."

    return AnomalyReport(
        has_anomaly=has_anomaly,
        anomaly_score=anomaly_score,
        anomaly_flags=flags,
        details=details
    )

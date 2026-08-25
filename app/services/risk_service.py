import re

# Türkçe ve İngilizce kritiklik seviyelerine göre ağırlıklandırılmış güvenlik ve kriz anahtar kelimeleri
HIGH_RISK_KEYWORDS = [
    # İngilizce
    "data breach", "zero-day", "exploit", "ransomware", "malware", 
    "data leak", "system compromise", "backdoor", "data loss", "exfiltration", "hijack",
    # Türkçe
    "veri sızıntısı", "veri sizintisi", "sıfır gün", "sifir gun", "fidye yazılımı", "fidye yazilimi", 
    "zararlı yazılım", "zararli yazilim", "kötü amaçlı yazılım", "kotu amacli yazilim", 
    "sızma testi", "sizma testi", "arka kapı", "arka kapi", "veri kaybı", "veri kaybi", 
    "bilgi sızıntısı", "bilgi sizintisi", "veri hırsızlığı", "veri hirsizligi", 
    "sistem ele geçirme", "sistem ele gecirme", "yetkisiz erişim", "yetkisiz erisim"
]

MEDIUM_RISK_KEYWORDS = [
    # İngilizce
    "cyber attack", "vulnerability", "security threat", "system failure", "critical outage", 
    "emergency state", "urgent incident", "phishing attack", "server crash", "infrastructure failure",
    # Türkçe
    "siber saldırı", "siber saldiri", "güvenlik zafiyeti", "guvenlik zafiyeti", "güvenlik açığı", "guvenlik acigi", 
    "siber tehdit", "siber olay", "güvenlik olayı", "olay müdahalesi", "olay mudahalesi",
    "kritik arıza", "kritik ariza", "acil müdahale", "acil mudahale", "acil durum", 
    "oltalama saldırısı", "oltalama saldirisi", "sistem çökmesi", "sistem cokmesi", "güvenlik ihlali"
]

LOW_RISK_KEYWORDS = [
    # İngilizce
    "security warning", "suspicious activity", "security patch", "audit finding", 
    "security alert", "system anomaly", "urgent update", "maintenance window",
    # Türkçe
    "güvenlik uyarısı", "guvenlik uyarisi", "şüpheli aktivite", "supheli aktivite", 
    "güvenlik yaması", "guvenlik yamasi", "denetim bulgusu", "güvenlik alarmı", 
    "guvenlik alarmi", "sistem anomalisi", "acil güncelleme", "acil guncelleme", "güvenlik tedbiri"
]

RISK_MITIGATORS = [
    "historical attack", "historical report", "past incident", "no systems affected", 
    "no current threat", "remediated", "resolved", "simulation", "test scenario", 
    "gecmis olay", "etkilenen sistem yok", "gecmiste kalmis", "simulasyon", "test raporu",
    "giderildi", "cozuldu"
]

RISK_AMPLIFIERS = [
    "active attack", "currently compromised", "ongoing breach", "unprecedented attack",
    "urgent action required", "devam eden saldiri", "halihazırda", "canli sistemler etkilendi",
    "kritik tehdit devam ediyor"
]

def _normalize_text(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()

def analyze_risk(text: str) -> dict:
    """
    Metindeki risk göstergelerini çok dilli (Türkçe & İngilizce) tam kelime grubu eşleşmesi,
    bağlamsal hafifleticiler (tarihi olay/simülasyon) ve aktif arttırıcılar ile analiz eder.
    """
    if not text or not text.strip():
        return {"risk_score": 0, "risk_level": "Low", "incident_status": "Genel Doküman"}
        
    text_normalized = _normalize_text(text)
    
    high_count = 0
    for kw in HIGH_RISK_KEYWORDS:
        pattern = rf"\b{re.escape(_normalize_text(kw))}\b"
        high_count += len(re.findall(pattern, text_normalized))
        
    med_count = 0
    for kw in MEDIUM_RISK_KEYWORDS:
        pattern = rf"\b{re.escape(_normalize_text(kw))}\b"
        med_count += len(re.findall(pattern, text_normalized))
        
    low_count = 0
    for kw in LOW_RISK_KEYWORDS:
        pattern = rf"\b{re.escape(_normalize_text(kw))}\b"
        low_count += len(re.findall(pattern, text_normalized))
    
    mitigator_count = sum(1 for kw in RISK_MITIGATORS if _normalize_text(kw) in text_normalized)
    amplifier_count = sum(1 for kw in RISK_AMPLIFIERS if _normalize_text(kw) in text_normalized)

    # Ağırlıklı risk skoru hesaplama (High: 3 puan, Medium: 2 puan, Low: 1 puan)
    raw_score = (high_count * 3) + (med_count * 2) + (low_count * 1)
    
    # Bağlamsal hafifletme: Eğer olay geçmişe ait veya simülasyon ise ve aktif tehdit yoksa skoru yarıya indir
    if mitigator_count > 0 and amplifier_count == 0:
        weighted_score = max(1, int(raw_score * 0.5))
        incident_status = "Tarihi / Çözülmüş Rapor (Aktif Tehdit Yok)"
    elif amplifier_count > 0:
        weighted_score = raw_score + (amplifier_count * 3)
        incident_status = "🚨 Aktif Canlı Saldırı / Olay"
    elif raw_score > 0:
        weighted_score = raw_score
        incident_status = "Potansiyel Risk / Analiz Raporu"
    else:
        weighted_score = 0
        incident_status = "Düşük Risk / Genel Doküman"

    if weighted_score == 0 or weighted_score <= 4:
        level = "Low"
    elif weighted_score <= 10:
        level = "Medium"
    else:
        level = "High"
        
    return {
        "risk_score": weighted_score,
        "risk_level": level,
        "incident_status": incident_status,
        "is_mitigated": mitigator_count > 0 and amplifier_count == 0
    }
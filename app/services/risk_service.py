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

def _normalize_text(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()

def analyze_risk(text: str) -> dict:
    """
    Metindeki risk göstergelerini çok dilli (Türkçe & İngilizce) tam kelime grubu eşleşmesi
    ve ağırlıklı skorlama ile analiz eder.
    """
    if not text or not text.strip():
        return {"risk_score": 0, "risk_level": "Low"}
        
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
    
    # Ağırlıklı risk skoru hesaplama (High: 3 puan, Medium: 2 puan, Low: 1 puan)
    weighted_score = (high_count * 3) + (med_count * 2) + (low_count * 1)
    
    if weighted_score == 0:
        level = "Low"
    elif weighted_score <= 4:
        level = "Low"
    elif weighted_score <= 10:
        level = "Medium"
    else:
        level = "High"
        
    return {
        "risk_score": weighted_score,
        "risk_level": level
    }
import re

# Türkçe ve İngilizce kritiklik seviyelerine göre ağırlıklandırılmış anahtar kelimeler
HIGH_RISK_KEYWORDS = [
    # İngilizce
    "breach", "zero-day", "exploit", "ransomware", "malware", 
    "leak", "compromise", "backdoor", "data loss", "exfiltration", "hijack",
    # Türkçe
    "sızıntı", "sizinti", "sıfır gün", "sifir gun", "fidye yazılımı", "fidye yazilimi", 
    "zararlı yazılım", "zararli yazilim", "kötü amaçlı yazılım", "kotu amacli yazilim", 
    "sızma", "sizma", "arka kapı", "arka kapi", "veri kaybı", "veri kaybi", 
    "veri sızıntısı", "veri sizintisi", "bilgi sızıntısı", "bilgi sizintisi", 
    "veri hırsızlığı", "veri hirsizligi", "ele geçirme", "ele gecirme"
]

MEDIUM_RISK_KEYWORDS = [
    # İngilizce
    "attack", "vulnerability", "threat", "failure", "critical", 
    "emergency", "urgent", "unauthorized", "phishing", "incident", "crash", "outage",
    # Türkçe
    "saldırı", "saldiri", "zafiyet", "güvenlik açığı", "güvenlik acigi", 
    "tehdit", "arıza", "ariza", "kritik", "acil durum", "acil", "yetkisiz", 
    "oltalama", "olay", "çökme", "cokme", "kesinti", "ihlal", "tehlike", "aksama"
]

LOW_RISK_KEYWORDS = [
    # İngilizce
    "warning", "suspicious", "patch", "audit", "alert", "anomaly", "update", "maintenance",
    # Türkçe
    "uyarı", "uyari", "şüpheli", "supheli", "yama", "denetim", 
    "alarm", "anomali", "güncelleme", "guncelleme", "bakım", "bakim", "tedbir"
]

def _normalize_text(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()

def analyze_risk(text: str) -> dict:
    """
    Metindeki risk göstergelerini çok dilli (Türkçe & İngilizce) tam kelime eşleşmesi
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
import re

# Kritiklik seviyelerine göre ağırlıklandırılmış anahtar kelimeler
HIGH_RISK_KEYWORDS = [
    "breach", "zero-day", "exploit", "ransomware", "malware", 
    "leak", "compromise", "backdoor", "data loss", "exfiltration"
]

MEDIUM_RISK_KEYWORDS = [
    "attack", "vulnerability", "threat", "failure", "critical", 
    "emergency", "urgent", "unauthorized", "phishing", "incident"
]

LOW_RISK_KEYWORDS = [
    "warning", "suspicious", "patch", "audit", "alert", "anomaly"
]

def analyze_risk(text: str) -> dict:
    """
    Metindeki risk göstergelerini tam kelime eşleşmesi (regex word boundary)
    ve ağırlıklı skorlama ile analiz eder.
    """
    if not text:
        return {"risk_score": 0, "risk_level": "Low"}
        
    text_lower = text.lower()
    
    high_count = sum(len(re.findall(rf"\b{re.escape(kw)}\b", text_lower)) for kw in HIGH_RISK_KEYWORDS)
    med_count = sum(len(re.findall(rf"\b{re.escape(kw)}\b", text_lower)) for kw in MEDIUM_RISK_KEYWORDS)
    low_count = sum(len(re.findall(rf"\b{re.escape(kw)}\b", text_lower)) for kw in LOW_RISK_KEYWORDS)
    
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
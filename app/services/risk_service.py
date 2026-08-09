RISK_KEYWORDS = [
    "breach", "attack", "failure", "critical", 
    "vulnerability", "urgent", "emergency", "threat", "leak"
]

def analyze_risk(text: str) -> dict:
    text_lower = text.lower()
    score = 0
    
    for word in RISK_KEYWORDS:
        score += text_lower.count(word)
        
    if score <= 2:
        level = "Low"
    elif score <= 5:
        level = "Medium"
    else:
        level = "High"
        
    return {"risk_score": score, "risk_level": level}
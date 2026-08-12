import re

# Genişletilmiş ve ağırlıklandırılmış kategori sözlüğü
CATEGORY_KEYWORDS = {
    "Cyber Security": [
        "vulnerability", "breach", "attack", "malware", "hack", "zero-day", "firewall", 
        "leak", "cyber", "confidential", "incident", "unauthorized", "credential", 
        "ransomware", "phishing", "ddos", "exploit", "trojan", "spyware", "penetration",
        "threat", "payload", "compromise", "backdoor", "cve"
    ],
    "Finance": [
        "revenue", "profit", "loss", "financial", "quarterly", "investment", "money", 
        "economy", "shares", "market", "expense", "cash", "growth", "margin", "dividend", 
        "fiscal", "asset", "capital", "budget", "balance sheet", "investor", "stock", 
        "accounting", "ebitda", "valuation", "tax", "banking"
    ],
    "Healthcare": [
        "patient", "hospital", "doctor", "medical", "disease", "clinical", "treatment", 
        "health", "drug", "symptoms", "therapy", "illness", "acute", "fever", "respiratory", 
        "diagnosis", "vaccine", "clinic", "surgery", "physician", "infection", "medicine",
        "pathology", "cardiac", "oncology"
    ],
    "Education": [
        "school", "university", "student", "teacher", "exam", "class", "study", "education", 
        "lecture", "learn", "course", "homework", "academic", "college", "grade", "degree", 
        "professor", "curriculum", "classroom", "faculty", "pedagogy"
    ],
    "Legal": [
        "contract", "agreement", "law", "lawsuit", "lawyer", "legal", "court", "regulation", 
        "compliance", "policy", "terms", "litigation", "liability", "clause", "jurisdiction", 
        "statutory", "attorney", "statute", "indemnification", "arbitration"
    ],
    "Technology": [
        "software", "hardware", "artificial intelligence", "ai", "computer", "algorithm", 
        "code", "database", "system", "engineering", "cloud", "network", "developer", 
        "server", "programming", "frontend", "backend", "machine learning", "api", "framework"
    ]
}

def predict_category(text: str) -> str:
    """
    Yüksek hızlı, bellek dostu ve deterministik kural tabanlı kategori sınıflandırıcısı.
    Render 512MB RAM sınırına takılmadan anında sonuç verir.
    """
    if not text or not text.strip():
        return "General"
        
    lower_text = text.lower()
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # Tam kelime eşleşmesi ile skor hesaplama
            pattern = rf"\b{re.escape(kw)}\b"
            matches = len(re.findall(pattern, lower_text))
            score += matches
        scores[category] = score

    # En yüksek skora sahip kategoriyi bul
    best_category = max(scores, key=scores.get)
    
    if scores[best_category] > 0:
        return best_category
        
    return "Technology"  # Varsayılan fallback
import re
from typing import Dict, Any, List, Optional

TECH_KEYWORDS = [
    "python", "java", "c#", ".net", "c++", "javascript", "typescript", "react", "angular", "vue",
    "html", "css", "sql", "postgresql", "mysql", "mongodb", "neo4j", "redis", "elasticsearch",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "spark", "pyspark", "hadoop",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "rest api", "fastapi", "flask",
    "django", "spring boot", "solidity", "blazor", "pyqt5", "postman", "tcp/udp", "iptables"
]

CV_TRIGGER_KEYWORDS = [
    "özgeçmiş", "ozgecmis", "curriculum vitae", "resume", "work experience", "iş deneyimi",
    "eğitim geçmişi", "education", "yetenekler", "skills", "teknik beceriler", "proje geçmişi",
    "sertifikalar", "iletisim bilgileri", "iletişim bilgileri"
]

def is_cv_document(text: str) -> bool:
    """Metnin bir CV / Özgeçmiş belgesi olup olmadığını tespit eder."""
    if not text:
        return False
    text_lower = text.lower()
    matches = sum(1 for kw in CV_TRIGGER_KEYWORDS if kw in text_lower)
    if matches >= 1 or any(strong in text_lower for strong in ["özgeçmiş", "ozgecmis", "curriculum vitae", "resume"]):
        return True
    return False

def analyze_cv_document(text: str) -> Dict[str, Any]:
    """
    CV / Özgeçmiş dokümanı için teknik yetenek seti, iletişim/PII durumu ve
    uzmanlaşma alanı önerisi üreten Doküman Zekası servisi.
    """
    if not text:
        return {
            "is_cv": False,
            "detected_tech_stack": [],
            "specialization": "Belirlenemedi"
        }

    text_lower = text.lower()
    is_cv = is_cv_document(text)

    # 1. Tech Stack Ayıklama
    detected_tech = []
    for tech in TECH_KEYWORDS:
        pattern = rf"\b{re.escape(tech)}\b"
        if re.search(pattern, text_lower):
            detected_tech.append(tech.title() if len(tech) <= 4 else tech.capitalize())

    detected_tech = list(dict.fromkeys(detected_tech))

    # 2. Uzmanlaşma Alanı Tahmini
    tech_set = {t.lower() for t in detected_tech}
    
    data_score = sum(1 for t in ["python", "pandas", "spark", "pyspark", "sql", "neo4j", "numpy", "hadoop"] if t in tech_set)
    backend_score = sum(1 for t in ["java", "c#", ".net", "python", "fastapi", "spring boot", "postgresql", "mysql"] if t in tech_set)
    devops_score = sum(1 for t in ["docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "iptables"] if t in tech_set)
    web_score = sum(1 for t in ["javascript", "typescript", "react", "angular", "vue", "html", "css", "blazor"] if t in tech_set)

    scores = [
        ("Veri Mühendisliği & Büyük Veri Analitiği", data_score),
        ("Backend & Yazılım Geliştirme", backend_score),
        ("Bulut Mimarisi & DevOps", devops_score),
        ("Web & Frontend Geliştirme", web_score)
    ]
    
    scores.sort(key=lambda x: x[1], reverse=True)
    best_spec = scores[0][0] if scores[0][1] > 0 else "Genel BT / Yazılım Profili"

    return {
        "is_cv": is_cv,
        "detected_tech_stack": detected_tech,
        "specialization": best_spec if is_cv else "CV Dokümanı Değil",
        "tech_count": len(detected_tech)
    }

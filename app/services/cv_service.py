import re
from typing import Dict, Any, List

TECH_KEYWORDS = [
    "python", "java", "c#", ".net", "c++", "javascript", "typescript", "react", "angular", "vue",
    "html", "css", "sql", "postgresql", "mysql", "mongodb", "neo4j", "redis", "elasticsearch",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "spark", "pyspark", "hadoop",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "rest api", "fastapi", "flask",
    "django", "spring boot", "solidity", "blazor", "pyqt5", "postman", "tcp/udp", "iptables",
    "node.js", "nodejs", "php", "ruby", "go", "rust", "kotlin", "swift", "scala",
    "tableau", "power bi", "excel", "airflow", "kafka", "rabbitmq", "graphql", "grpc",
]

# Güçlü CV sinyalleri — tek bir eşleşme yeterli
CV_STRONG_SIGNALS = [
    "özgeçmiş", "ozgecmis", "curriculum vitae", "curriculum vitæ",
    "resume", "cv template", "professional summary", "kariyer özeti",
    "kariyer profili", "work experience", "iş deneyimi", "is deneyimi",
    "eğitim geçmişi", "egitim gecmisi", "eğitim bilgileri",
    "teknik beceriler", "technical skills", "yetenekler ve beceriler",
    "sertifikalar", "certifications", "professional certifications",
    "referanslar", "references", "iletişim bilgileri",
    "proje geçmişi", "selected projects", "kişisel projeler",
    "internship", "staj", "staj deneyimi",
    # Yaygın bölüm başlıkları
    "work history", "employment history", "professional experience",
    "key skills", "core competencies", "areas of expertise",
    "education background", "academic background",
    # LinkedIn / GitHub
    "linkedin.com/in/", "github.com/",
]

# Zayıf sinyaller — kombinasyonla kullanılır (en az 2 tane)
CV_WEAK_SIGNALS = [
    "deneyim", "experience", "skills", "beceri",
    "eğitim", "education", "proje", "project",
    "ödül", "award", "yayın", "publication",
    "dil bilgisi", "languages", "hobbies",
    "objective", "hedef",
]


def is_cv_document(text: str) -> bool:
    """
    CV / Özgeçmiş tespiti — güçlü sinyal veya iki zayıf sinyal kombinasyonu.
    Yanlış pozitifi önlemek için eşik yükseltilmiştir.
    """
    if not text:
        return False
    text_lower = text.lower()

    # Güçlü sinyal: tek eşleşme yeterli
    for signal in CV_STRONG_SIGNALS:
        if signal in text_lower:
            return True

    # Zayıf sinyaller: en az 2 farklı sinyal gerekli
    weak_matches = sum(1 for s in CV_WEAK_SIGNALS if s in text_lower)
    return weak_matches >= 2


def extract_cv_sections(text: str) -> Dict[str, str]:
    """
    CV bölümlerini (özet, deneyim, eğitim, beceriler, projeler, iletişim)
    metnin yapısından ayıklar.
    """
    sections: Dict[str, str] = {}

    # Bölüm başlıkları regex'i
    section_patterns = {
        "summary": r"(?:professional summary|kariyer özeti|özet|objective|profil)\s*:?\s*\n(.*?)(?=\n[A-ZÇĞİÖŞÜ][^\n]{2,50}\n|\Z)",
        "experience": r"(?:work experience|iş deneyimi|is deneyimi|employment history|professional experience)\s*:?\s*\n(.*?)(?=\n[A-ZÇĞİÖŞÜ][^\n]{2,50}\n|\Z)",
        "education": r"(?:education|eğitim|egitim|academic background)\s*:?\s*\n(.*?)(?=\n[A-ZÇĞİÖŞÜ][^\n]{2,50}\n|\Z)",
        "skills": r"(?:skills|beceriler|teknik beceriler|technical skills|key skills)\s*:?\s*\n(.*?)(?=\n[A-ZÇĞİÖŞÜ][^\n]{2,50}\n|\Z)",
        "projects": r"(?:projects|projeler|selected projects|kişisel projeler)\s*:?\s*\n(.*?)(?=\n[A-ZÇĞİÖŞÜ][^\n]{2,50}\n|\Z)",
    }

    for section_name, pattern in section_patterns.items():
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            content = m.group(1).strip()[:500]  # Maks 500 karakter
            if content:
                sections[section_name] = content

    return sections


def analyze_cv_document(text: str) -> Dict[str, Any]:
    """
    CV / Özgeçmiş dokümanı için teknik yetenek seti, iletişim/PII durumu ve
    uzmanlaşma alanı önerisi üreten Doküman Zekası servisi.

    Hallucination önleme:
    - is_cv tespiti güçlü sinyal tabanlıdır
    - specialization yalnızca gerçek teknik etiketlerden üretilir
    - Bölüm çıkarımı regex tabanlı (LLM değil)
    """
    if not text:
        return {"is_cv": False, "detected_tech_stack": [], "specialization": "Belirlenemedi"}

    text_lower = text.lower()
    is_cv = is_cv_document(text)

    # 1. Tech Stack Ayıklama
    detected_tech: List[str] = []
    for tech in TECH_KEYWORDS:
        pattern = rf"\b{re.escape(tech)}\b"
        if re.search(pattern, text_lower):
            detected_tech.append(tech.upper() if len(tech) <= 3 else tech.title())
    detected_tech = list(dict.fromkeys(detected_tech))

    # 2. Uzmanlaşma Alanı Tahmini (gerçek teknoloji sayısına dayalı)
    tech_set = {t.lower() for t in detected_tech}

    data_score    = sum(1 for t in ["python", "pandas", "spark", "pyspark", "sql", "neo4j", "numpy", "hadoop", "airflow", "kafka"] if t in tech_set)
    backend_score = sum(1 for t in ["java", "c#", ".net", "python", "fastapi", "spring boot", "postgresql", "mysql", "node.js", "grpc"] if t in tech_set)
    devops_score  = sum(1 for t in ["docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "iptables", "terraform"] if t in tech_set)
    web_score     = sum(1 for t in ["javascript", "typescript", "react", "angular", "vue", "html", "css", "blazor", "graphql"] if t in tech_set)
    security_score= sum(1 for t in ["iptables", "penetration", "kali", "metasploit", "wireshark", "nmap", "burp"] if t in tech_set)
    ml_score      = sum(1 for t in ["tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy", "machine learning"] if t in tech_set)

    scores = [
        ("Veri Mühendisliği & Büyük Veri Analitiği", data_score),
        ("Backend & Yazılım Geliştirme", backend_score),
        ("Bulut Mimarisi & DevOps", devops_score),
        ("Web & Frontend Geliştirme", web_score),
        ("Siber Güvenlik", security_score),
        ("Makine Öğrenimi & Yapay Zeka", ml_score),
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    best_spec = scores[0][0] if scores[0][1] > 0 else "Genel BT / Yazılım Profili"

    # 3. CV Bölümlerini Ayıkla
    sections = extract_cv_sections(text) if is_cv else {}

    # 4. Sosyal Profil Linkleri
    social_links: List[str] = []
    for platform in ["linkedin.com/in/", "github.com/", "twitter.com/", "instagram.com/"]:
        m = re.search(rf"\b{re.escape(platform)}[\w.\-/]+", text_lower)
        if m:
            social_links.append(m.group())

    return {
        "is_cv": is_cv,
        "detected_tech_stack": detected_tech,
        "specialization": best_spec if is_cv else "CV Dokümanı Değil",
        "tech_count": len(detected_tech),
        "sections_found": list(sections.keys()),
        "social_profiles": social_links,
    }

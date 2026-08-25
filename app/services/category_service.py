import re
from typing import Tuple

# ─────────────────────────────────────────────────────────────────
# CONTROLLED TAXONOMY — Deterministic sınıflandırma (P0 fix)
# Kimlik kartı "Literature" olarak sınıflandırılma sorunu bu
# dosyanın yeniden yazılmasıyla kalıcı olarak çözülmüştür.
# ─────────────────────────────────────────────────────────────────

# Öncelik 1 — Kesin eşleşme: Bu kalıplar bulunursa diğer kategoriler denenmez
EXACT_MATCH_RULES: list[Tuple[str, list[str]]] = [
    ("IDENTITY_CARD", [
        # Türkçe kimlik kartı / nüfus cüzdanı
        "türkiye cumhuriyeti kimlik", "tc kimlik karti", "t.c. kimlik",
        "nüfus cüzdanı", "nufus cuzdani", "kimlik kartı", "kimlik karti",
        "republic of turkey identity", "turkish identity card",
        "ulusal kimlik", "national id",
        # Pasaport
        "pasaport", "passport", "travel document", "seyahat belgesi",
        # Sürücü belgesi
        "sürücü belgesi", "surucu belgesi", "driving licence", "driver license",
        # MRZ
        "i<tur", "p<tur",
        # Kimlik alanı kalıpları
        "soyad / surname", "ad / given name", "doğum tarihi / date of birth",
        "geçerlilik tarihi / expiry", "belge no / document no",
        "anne adı", "baba adı", "mother's name", "father's name",
        "uyruk / nationality", "cinsiyet / sex",
    ]),
    ("RESUME_CV", [
        "özgeçmiş", "ozgecmis", "curriculum vitae", "cv template",
        "work experience", "iş deneyimi", "is deneyimi",
        "professional summary", "kariyer özeti", "kariyer ozeti",
        "eğitim geçmişi", "egitim gecmisi",
        "teknik beceriler", "technical skills",
        "sertifikalar", "certifications", "certificates",
        "internship", "staj", "referans", "references",
        "linkedin.com/in/", "github.com/",
        "proje geçmişi", "projects",
    ]),
    ("BANK_DOCUMENT", [
        "hesap ekstresi", "account statement", "bank statement",
        "iban:", "swift:", "bic:", "banka dekontu",
        "ekstre tarihi", "statement date", "bakiye / balance",
    ]),
    ("INVOICE", [
        "fatura no", "invoice no", "invoice number", "fatura tarihi",
        "kdv tutarı", "kdv no", "kdv dahil", "vergi no",
        "fatura toplam", "invoice total", "vergisi:", "kdv %",
        "fatura\n", "e-fatura",
    ]),
    ("CONTRACT", [
        "sözleşme", "sozlesme", "hizmet sözleşmesi", "kira sözleşmesi",
        "iş sözleşmesi", "service agreement", "employment contract",
        "rental agreement", "lease agreement", "gizlilik sözleşmesi",
        "nda", "non-disclosure agreement",
    ]),
    ("MEDICAL_DOCUMENT", [
        "hasta adı", "patient name", "hasta tc", "tc kimlik no:", "doğum tarihi:",
        "teşhis", "diagnosis", "reçete", "prescription", "ilaç adı",
        "poliklinik", "klinik raporu", "tıbbi rapor", "medical report",
        "hastane:", "hospital:", "doktor:", "hekim:",
    ]),
    ("ACADEMIC_DOCUMENT", [
        "transkript", "transcript", "öğrenci no", "student id",
        "not dökümü", "grade report", "diploma", "sertifika",
        "üniversite:", "university:", "fakülte:", "faculty:",
        "mezuniyet belgesi", "graduation certificate",
    ]),
    ("LEGAL_DOCUMENT", [
        "mahkeme kararı", "court decision", "karar no", "dava no",
        "yargı", "yargi", "hakim", "savcı", "avukat imzası",
        "hukuk bürosu", "law firm", "kanun no", "madde:",
    ]),
    ("SECURITY_INCIDENT", [
        "incident report", "olay raporu", "güvenlik olayı",
        "veri ihlali", "data breach", "güvenlik açığı tespit",
        "saldırı zaman çizelgesi", "etkilenen sistemler",
        "tehdit aktörü", "threat actor", "ioc:", "indicator of compromise",
        "sızma raporu", "pentest report",
    ]),
]

# Öncelik 2 — Anahtar kelime skoru tabanlı sınıflandırma
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "SECURITY_INCIDENT": [
        "vulnerability", "breach", "malware", "hack", "zero-day", "firewall",
        "data leak", "cyber", "ransomware", "phishing", "ddos", "exploit", "trojan",
        "spyware", "penetration test", "cyber threat", "payload", "backdoor", "cve",
        "intrusion detection", "cyber security", "cyber attack", "credential theft",
        "zafiyet", "güvenlik açığı", "zararlı yazılım", "kötü amaçlı yazılım",
        "hack", "sızma testi", "güvenlik duvarı", "veri sızıntısı",
        "siber", "siber saldırı", "siber tehdit", "siber olay",
        "yetkisiz erişim", "fidye yazılımı", "oltalama saldırısı",
        "truva atı", "casus yazılım", "arka kapı", "bilgi güvenliği",
    ],
    "FINANCIAL_REPORT": [
        "revenue", "profit", "loss", "financial", "quarterly", "investment", "money",
        "economy", "shares", "market", "expense", "cash", "growth", "margin", "dividend",
        "fiscal", "asset", "capital", "budget", "balance sheet", "investor", "stock",
        "accounting", "ebitda", "valuation", "tax", "banking", "interest", "inflation",
        "gelir", "kâr", "zarar", "finansal", "çeyrek", "yatırım", "para", "ekonomi",
        "hisse", "piyasa", "gider", "nakit", "büyüme", "marj", "temettü",
        "mali", "varlık", "sermaye", "bütçe", "bilanço", "yatırımcı", "borsa",
        "muhasebe", "değerleme", "vergi", "bankacılık", "faiz", "enflasyon", "kredi",
    ],
    "HEALTHCARE": [
        "patient", "hospital", "doctor", "medical", "disease", "clinical", "treatment",
        "health", "drug", "symptoms", "therapy", "illness", "acute", "fever",
        "diagnosis", "vaccine", "clinic", "surgery", "physician", "infection",
        "hasta", "hastane", "doktor", "tıbbi", "hastalık", "klinik",
        "tedavi", "sağlık", "ilaç", "belirti", "semptom", "terapi",
        "enfeksiyon", "ateş", "teşhis", "aşı", "cerrahi", "hekim",
    ],
    "EDUCATION": [
        "school", "university", "student", "teacher", "exam", "class", "education",
        "lecture", "course", "academic", "college", "grade", "degree",
        "professor", "curriculum", "classroom", "faculty", "pedagogy",
        "okul", "üniversite", "öğrenci", "öğretmen", "sınav", "sınıf",
        "ders", "eğitim", "akademik", "fakülte", "profesör",
        "müfredat", "diploma", "ödev", "kampüs",
    ],
    "LEGAL": [
        "contract", "agreement", "law", "lawsuit", "lawyer", "legal", "court",
        "regulation", "compliance", "policy", "litigation", "liability", "clause",
        "jurisdiction", "statutory", "attorney", "legislation",
        "anlaşma", "hukuk", "yasa", "dava", "avukat", "mahkeme",
        "düzenleme", "mevzuat", "uyumluluk", "tazminat", "yükümlülük",
        "kanun", "tahkim", "ihtilaf", "hak", "vekalet",
    ],
    "TECHNOLOGY": [
        "software", "hardware", "artificial intelligence", "computer", "algorithm",
        "code", "database", "system", "engineering", "cloud", "network", "developer",
        "server", "programming", "machine learning", "api", "framework",
        "yazılım", "donanım", "yapay zeka", "algoritma", "kod",
        "veritabanı", "sistem", "mühendislik", "bulut", "geliştirici",
        "sunucu", "programlama", "makine öğrenimi", "model", "bilişim",
    ],
    "LITERATURE_ARTS": [
        "literature", "novel", "fiction", "poem", "poetry", "author",
        "literary", "protagonist", "drama", "essay", "prose", "criticism",
        "folklore", "metaphor", "aesthetic",
        "edebiyat", "roman", "hikâye", "şair", "şiir", "anlatıcı",
        "tiyatro", "kahraman", "kurgu", "masal", "mesnevî", "tasavvuf",
    ],
}

DISPLAY_LABELS: dict[str, str] = {
    "IDENTITY_CARD":    "Kimlik / Pasaport Belgesi",
    "RESUME_CV":        "Özgeçmiş / CV",
    "BANK_DOCUMENT":    "Banka / Finansal Belge",
    "INVOICE":          "Fatura",
    "CONTRACT":         "Sözleşme",
    "MEDICAL_DOCUMENT": "Tıbbi Belge",
    "ACADEMIC_DOCUMENT":"Akademik Belge",
    "LEGAL_DOCUMENT":   "Hukuki Belge",
    "SECURITY_INCIDENT":"Güvenlik Olayı / Siber Rapor",
    "FINANCIAL_REPORT": "Finansal Rapor",
    "HEALTHCARE":       "Sağlık Belgesi",
    "EDUCATION":        "Eğitim Belgesi",
    "LEGAL":            "Hukuk Belgesi",
    "TECHNOLOGY":       "Teknoloji Belgesi",
    "LITERATURE_ARTS":  "Edebiyat & Sanat",
    "GENERAL_DOCUMENT": "Genel Doküman",
}


def _normalize(text: str) -> str:
    return (
        text
        .replace("İ", "i").replace("I", "ı")
        .replace("Ğ", "ğ").replace("Ş", "ş")
        .replace("Ü", "ü").replace("Ö", "ö")
        .replace("Ç", "ç")
        .lower()
    )


def predict_category(text: str) -> str:
    """
    Deterministic taxonomy tabanlı çok adımlı sınıflandırıcı.

    Adım 1 — Exact-match (kesin eşleşme): Kontrollü anahtar ifade seti.
              Kimlik kartı, CV vb. dokümanlar burada yakalanır.
    Adım 2 — Keyword scoring: Frekans tabanlı ağırlık hesabı.
    Adım 3 — Fallback: GENERAL_DOCUMENT.

    Dönüş değeri: dahili kategori kodu (display_label için DISPLAY_LABELS kullanın).
    """
    if not text or not text.strip():
        return "GENERAL_DOCUMENT"

    normalized = _normalize(text)

    # ── Adım 1: Exact-match kontrolü ──────────────────────────────
    # Her kategori için minimum 1 sinyal yeterli (yüksek spesifite)
    for category, signals in EXACT_MATCH_RULES:
        for signal in signals:
            if _normalize(signal) in normalized:
                return category

    # ── Adım 2: Keyword scoring ────────────────────────────────────
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            pattern = rf"\b{re.escape(_normalize(kw))}\b"
            score += len(re.findall(pattern, normalized))
        scores[category] = score

    best = max(scores, key=lambda k: scores[k])
    if scores[best] > 0:
        return best

    # ── Adım 3: Fallback ───────────────────────────────────────────
    return "GENERAL_DOCUMENT"


def get_category_label(code: str) -> str:
    """Dahili kategori kodunu insan tarafından okunabilir Türkçe etikete çevirir."""
    return DISPLAY_LABELS.get(code, code)
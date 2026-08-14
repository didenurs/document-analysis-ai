import re

# Türkçe ve İngilizce destekli zenginleştirilmiş kategori anahtar kelime sözlüğü
CATEGORY_KEYWORDS = {
    "Cyber Security": [
        # İngilizce
        "vulnerability", "breach", "malware", "hack", "zero-day", "firewall", 
        "data leak", "cyber", "ransomware", "phishing", "ddos", "exploit", "trojan", 
        "spyware", "penetration test", "cyber threat", "payload", "backdoor", "cve", 
        "intrusion detection", "cyber security", "cyber attack", "data breach", "credential theft",
        # Türkçe
        "zafiyet", "güvenlik açığı", "güvenlik acigi", "zararlı yazılım", "zararli yazilim", 
        "kötü amaçlı yazılım", "kotu amacli yazilim", "hack", "sızma testi", "sizma testi", 
        "güvenlik duvarı", "guvenlik duvari", "veri sızıntısı", "veri sizintisi", 
        "siber", "siber saldırı", "siber saldiri", "siber tehdit", "siber olay", "güvenlik olayı",
        "yetkisiz erişim", "fidye yazılımı", "fidye yazilimi", "oltalama saldırısı", 
        "truva atı", "truva ati", "casus yazılım", "casus yazilimi", "arka kapı", "arka kapi", 
        "bilgi güvenliği", "ağ güvenliği"
    ],
    "Literature & Arts": [
        # İngilizce
        "literature", "novel", "story", "fiction", "poem", "poetry", "author", "narrator", 
        "plot", "literary", "protagonist", "character", "art", "theme", "narrative", "drama", 
        "essay", "prose", "book", "criticism", "folklore", "metaphor", "aesthetic",
        # Türkçe
        "öykü", "oyku", "öykücülük", "oykuculuk", "roman", "hikâye", "hikaye", "edebiyat", 
        "yazar", "şair", "sair", "şiir", "siir", "anlatıcı", "anlatici", "olay örgüsü", 
        "olay orgusu", "sanat", "tiyatro", "karakter", "kahraman", "kurgu", "metin", 
        "masal", "mesnevî", "mesnevi", "kıssa", "kissa", "menkıbe", "menkibe", "makale", 
        "eser", "tasavvuf", "tema", "yapıt", "yapit", "üslup", "uslup", "anlatı", "anlati", "kitap"
    ],
    "Finance": [
        # İngilizce
        "revenue", "profit", "loss", "financial", "quarterly", "investment", "money", 
        "economy", "shares", "market", "expense", "cash", "growth", "margin", "dividend", 
        "fiscal", "asset", "capital", "budget", "balance sheet", "investor", "stock", 
        "accounting", "ebitda", "valuation", "tax", "banking", "interest", "inflation", "credit",
        # Türkçe
        "gelir", "kâr", "kar", "zarar", "finansal", "finans", "çeyrek", "ceyrek", "yatırım", 
        "yatirim", "para", "ekonomi", "hisse", "piyasa", "gider", "nakit", "büyüme", "buyume", 
        "marj", "temettü", "temettu", "mali", "varlık", "varlik", "sermaye", "bütçe", "butce", 
        "bilanço", "bilanco", "yatırımcı", "yatirimci", "borsa", "muhasebe", "değerleme", 
        "degerleme", "vergi", "bankacılık", "bankacilik", "faiz", "enflasyon", "kredi"
    ],
    "Healthcare": [
        # İngilizce
        "patient", "hospital", "doctor", "medical", "disease", "clinical", "treatment", 
        "health", "drug", "symptoms", "therapy", "illness", "acute", "fever", "respiratory", 
        "diagnosis", "vaccine", "clinic", "surgery", "physician", "infection", "medicine",
        "pathology", "cardiac", "oncology", "pharmacy",
        # Türkçe
        "hasta", "hastane", "doktor", "tıbbi", "tibbi", "hastalık", "hastalik", "klinik", 
        "tedavi", "sağlık", "saglik", "ilaç", "ilac", "belirti", "semptom", "terapi", 
        "enfeksiyon", "ateş", "ates", "solunum", "teşhis", "teshis", "aşı", "asi", 
        "cerrahi", "hekim", "tıp", "tip", "patoloji", "kardiyoloji", "onkoloji", "reçete", 
        "recete", "muayene", "eczane"
    ],
    "Education": [
        # İngilizce
        "school", "university", "student", "teacher", "exam", "class", "study", "education", 
        "lecture", "learn", "course", "homework", "academic", "college", "grade", "degree", 
        "professor", "curriculum", "classroom", "faculty", "pedagogy", "lesson",
        # Türkçe
        "okul", "üniversite", "universite", "öğrenci", "ogrenci", "öğretmen", "ogretmen", 
        "sınav", "sinav", "sınıf", "sinif", "ders", "eğitim", "egitim", "öğrenim", "ogrenim", 
        "öğretim", "ogretim", "akademik", "fakülte", "fakulte", "profesör", "profesor", 
        "müfredat", "mufredat", "not", "diploma", "ödev", "odev", "kampüs", "kampus", 
        "pedagoji", "mezuniyet", "öğretim üyesi"
    ],
    "Legal": [
        # İngilizce
        "contract", "agreement", "law", "lawsuit", "lawyer", "legal", "court", "regulation", 
        "compliance", "policy", "terms", "litigation", "liability", "clause", "jurisdiction", 
        "statutory", "attorney", "statute", "indemnification", "arbitration", "legislation",
        # Türkçe
        "sözleşme", "sozlesme", "anlaşma", "anlasma", "hukuk", "yasa", "dava", "avukat", 
        "mahkeme", "düzenleme", "duzenleme", "mevzuat", "uyumluluk", "politika", "hüküm", 
        "hukum", "tazminat", "yükümlülük", "yukumluluk", "madde", "yargı", "yargi", 
        "kanun", "tahkim", "ihtilaf", "kanuni", "duruşma", "durusma", "hak", "vekalet"
    ],
    "Technology": [
        # İngilizce
        "software", "hardware", "artificial intelligence", "ai", "computer", "algorithm", 
        "code", "database", "system", "engineering", "cloud", "network", "developer", 
        "server", "programming", "frontend", "backend", "machine learning", "api", "framework",
        # Türkçe
        "yazılım", "yazilim", "donanım", "donanim", "yapay zeka", "algoritma", "kod", 
        "veritabanı", "veritabani", "sistem", "mühendislik", "muhendislik", "bulut", 
        "ağ", "ag", "geliştirici", "gelistirici", "sunucu", "programlama", "makine öğrenimi", 
        "makine ogrenimi", "model", "veri", "bilişim", "bilisim", "entegrasyon", "uygulama", 
        "dijital", "teknoloji"
    ]
}

def _normalize_text(text: str) -> str:
    """Türkçe ve İngilizce karakterleri normalize eder."""
    return text.replace("İ", "i").replace("I", "ı").lower()

def predict_category(text: str) -> str:
    """
    Yüksek hızlı, bellek dostu, çok dilli kural tabanlı kategori sınıflandırıcısı.
    Türkçe ve İngilizce dahil metinleri anında sınıflandırır.
    """
    if not text or not text.strip():
        return "General"
        
    lower_text = _normalize_text(text)
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            normalized_kw = _normalize_text(kw)
            pattern = rf"\b{re.escape(normalized_kw)}\b"
            matches = len(re.findall(pattern, lower_text))
            score += matches
        scores[category] = score

    # En yüksek skora sahip kategoriyi bul
    best_category = max(scores, key=scores.get)
    
    if scores[best_category] > 0:
        return best_category
        
    return "General"
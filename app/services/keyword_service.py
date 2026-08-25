import re
from typing import Optional, List
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from app.utils.language_detector import detect_language

MULTILINGUAL_STOPWORDS_LIST = [
    # English
    "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", "this",
    "are", "was", "were", "as", "by", "an", "be", "at", "from", "or", "which", "an",
    "have", "has", "had", "will", "would", "can", "could", "should", "their", "our",
    "about", "into", "more", "also", "some", "such", "than", "them", "very", "just",
    "these", "those", "been", "being", "hour", "hours", "standard", "time",
    # Turkish
    "bir", "ve", "bu", "ile", "için", "da", "de", "ise", "olan", "olarak", "gibi",
    "kadar", "daha", "çok", "en", "ancak", "veya", "tarafından", "şeklinde", "sonra",
    "önce", "üzere", "göre", "tüm", "her", "bazı", "diğer", "bunu", "bunun", "buna",
    "var", "yok", "kendi", "hem", "ya", "ne", "hangi", "nasıl", "neden", "çünkü",
    "şu", "öyle", "böyle", "şöyle", "artık", "zaten", "bile", "dahi", "yalnız", "ancak",
    "saat", "sularında", "son", "derece", "yeni", "büyük", "resmi"
]

CATEGORY_SPECIFIC_STOPWORDS = {
    "IDENTITY_CARD": [
        "türkiye", "cumhuriyeti", "kimlik", "karti", "kartı", "republic", "turkey",
        "identity", "card", "soyad", "soyadi", "soyadı", "surname", "ad", "adi", "adı",
        "given", "name", "names", "doğum", "dogum", "tarih", "tarihi", "birth", "date",
        "belge", "seri", "document", "validity", "geçerlilik", "gecerlilik", "valid",
        "until", "cinsiyet", "cinsiyeti", "sex", "gender", "uyruk", "uyruğu", "uyrugu",
        "nationality", "nüfus", "nufus", "cüzdanı", "cuzdani", "anne", "baba", "mother",
        "father", "imza", "signature", "kan", "grubu", "blood", "group", "mrz"
    ],
    "RESUME_CV": [
        "özgeçmiş", "ozgecmis", "curriculum", "vitae", "resume", "cv", "deneyim",
        "deneyimi", "experience", "work", "eğitim", "egitim", "education", "beceri",
        "beceriler", "skills", "profil", "profili", "summary", "tarih", "iletişim",
        "iletisim", "contact", "telefon", "email", "mail", "adres", "address", "proje",
        "projeler", "projects", "referans", "references", "sertifika", "certifications"
    ],
    "CONTRACT": [
        "sözleşme", "sozlesme", "madde", "maddesi", "taraf", "taraflar", "hizmet",
        "hüküm", "hükümleri", "imza", "tarih", "tarihinde", "agreement", "contract",
        "clause", "party", "parties", "terms", "conditions", "işbu", "tanzim", "kabul",
        "beyan", "taahhüt", "eder", "ederler"
    ],
    "INVOICE": [
        "fatura", "invoice", "tarih", "tarihi", "date", "toplam", "total", "tutar",
        "tutarı", "kdv", "vat", "tax", "no", "number", "numarası", "vkn", "vergi",
        "bedel", "ödenecek", "matrah", "miktar", "birim", "fiyat", "fiyatı"
    ],
    "BANK_DOCUMENT": [
        "hesap", "ekstre", "ekstresi", "statement", "bank", "banka", "iban", "swift",
        "bic", "dekont", "bakiye", "balance", "borç", "alacak", "tutar", "işlem", "tarihi"
    ]
}

def extract_keywords(
    text: str, 
    top_n: int = 5, 
    language: Optional[str] = None,
    category: Optional[str] = None
) -> List[str]:
    """
    Metinden çok dilli (Türkçe & İngilizce) ve doküman türüne duyarlı (Document-Type Aware)
    en önemli semantik anahtar ifadeleri çıkarır. Kimlik/CV/Sözleşme şablon kelimelerini eler.
    """
    if not text or not text.strip():
        return []
        
    lang = language or detect_language(text)
    stops = list(MULTILINGUAL_STOPWORDS_LIST)
    
    # Doküman tipine özel şablon/etiket kelimeleri de stopword olarak ekle
    if category and category in CATEGORY_SPECIFIC_STOPWORDS:
        stops.extend(CATEGORY_SPECIFIC_STOPWORDS[category])
        
    stops_set = set(stops)
    
    try:
        # N-Gram TF-IDF Tabanlı Hızlı Anahtar Kelime Çıkarımı
        vec = TfidfVectorizer(
            token_pattern=r'(?u)\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b',
            ngram_range=(1, 2),
            stop_words=stops,
            max_features=60
        )
        tfidf = vec.fit_transform([text])
        feature_names = vec.get_feature_names_out()
        scores = tfidf.toarray()[0]
        scored_keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        
        results = [
            kw for kw, s in scored_keywords 
            if len(kw.strip()) > 3 and kw.lower() not in stops_set
        ][:top_n]
        
        if results:
            return results
    except Exception:
        pass
        
    # Güvenli Kelime Frekansı Tabanlı Fallback
    words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stops_set and len(w) > 3]
    
    if not filtered:
        return [w for w in words if len(w) > 2 and w not in stops_set][:top_n]
        
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]
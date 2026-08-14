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

def extract_keywords(text: str, top_n: int = 5, language: Optional[str] = None) -> List[str]:
    """
    Metinden çok dilli (Türkçe & İngilizce) en önemli semantik anahtar ifadeleri
    yüksek hızda ve sıfır bellek yükü ile çıkarır.
    """
    if not text or not text.strip():
        return []
        
    lang = language or detect_language(text)
    stops = MULTILINGUAL_STOPWORDS_LIST if lang == "tr" else "english"
    
    try:
        # N-Gram TF-IDF Tabanlı Hızlı Anahtar Kelime Çıkarımı
        vec = TfidfVectorizer(
            token_pattern=r'(?u)\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b',
            ngram_range=(1, 2),
            stop_words=stops,
            max_features=40
        )
        tfidf = vec.fit_transform([text])
        feature_names = vec.get_feature_names_out()
        scores = tfidf.toarray()[0]
        scored_keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        
        results = [kw for kw, s in scored_keywords if len(kw.strip()) > 3][:top_n]
        if results:
            return results
    except Exception:
        pass
        
    # Güvenli Kelime Frekansı Tabanlı Fallback
    words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', text.lower())
    stop_set = set(MULTILINGUAL_STOPWORDS_LIST)
    filtered = [w for w in words if w not in stop_set and len(w) > 3]
    
    if not filtered:
        return [w for w in words if len(w) > 2][:top_n]
        
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]
import re
import gc
from typing import Optional, List
from collections import Counter
from keybert import KeyBERT
from app.utils.language_detector import detect_language

_kw_model = None

MULTILINGUAL_STOPWORDS_LIST = [
    # English
    "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", "this",
    "are", "was", "were", "as", "by", "an", "be", "at", "from", "or", "which", "an",
    "have", "has", "had", "will", "would", "can", "could", "should", "their", "our",
    "about", "into", "more", "also", "some", "such", "than", "them", "very", "just",
    "these", "those", "been", "being",
    # Turkish
    "bir", "ve", "bu", "ile", "için", "da", "de", "ise", "olan", "olarak", "gibi",
    "kadar", "daha", "çok", "en", "ancak", "veya", "tarafından", "şeklinde", "sonra",
    "önce", "üzere", "göre", "tüm", "her", "bazı", "diğer", "bunu", "bunun", "buna",
    "var", "yok", "kendi", "hem", "ya", "ne", "hangi", "nasıl", "neden", "çünkü",
    "şu", "öyle", "böyle", "şöyle", "artık", "zaten", "bile", "dahi", "yalnız", "ancak"
]

def _get_kw_model():
    global _kw_model
    if _kw_model is None:
        try:
            print("KeyBERT modeli yükleniyor... (all-MiniLM-L6-v2)")
            _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
            gc.collect()
        except Exception as e:
            print(f"KeyBERT yükleme hatası: {e}")
            _kw_model = None
    return _kw_model

def extract_keywords(text: str, top_n: int = 5, language: Optional[str] = None) -> List[str]:
    """
    Metinden çok dilli (Türkçe & İngilizce) en önemli semantik anahtar ifadeleri çıkarır.
    """
    if not text or not text.strip():
        return []
        
    lang = language or detect_language(text)
    stop_words_arg = MULTILINGUAL_STOPWORDS_LIST if lang == "tr" else "english"
    
    try:
        kw_model = _get_kw_model()
        if kw_model is not None:
            keywords = kw_model.extract_keywords(
                text, 
                keyphrase_ngram_range=(1, 2), 
                stop_words=stop_words_arg, 
                top_n=top_n
            )
            extracted = [kw[0] for kw in keywords if len(kw[0].strip()) > 2]
            if extracted:
                return extracted
    except Exception as e:
        print(f"KeyBERT çıkarım uyarısı: {e}")
        
    # Gelişmiş TF Tabanlı Çok Dilli Fallback
    words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', text.lower())
    stop_set = set(MULTILINGUAL_STOPWORDS_LIST)
    filtered = [w for w in words if w not in stop_set and len(w) > 3]
    
    if not filtered:
        return [w for w in words if len(w) > 2][:top_n]
        
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]
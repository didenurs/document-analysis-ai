from keybert import KeyBERT
import gc

_kw_model = None

def _get_kw_model():
    global _kw_model
    if _kw_model is None:
        print("KeyBERT modeli yükleniyor... (all-MiniLM-L6-v2)")
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        gc.collect()
    return _kw_model

def extract_keywords(text: str, top_n: int = 5) -> list:
    """
    Metinden en önemli semantik anahtar ifadeleri çıkarır.
    """
    if not text or not text.strip():
        return []
        
    try:
        kw_model = _get_kw_model()
        keywords = kw_model.extract_keywords(
            text, 
            keyphrase_ngram_range=(1, 2), 
            stop_words='english', 
            top_n=top_n
        )
        return [kw[0] for kw in keywords]
    except Exception as e:
        print(f"KeyBERT çıkarım uyarısı: {e}")
        # Basit fallback: en sık geçen anlamlı kelimeler
        words = [w.lower() for w in text.split() if len(w) > 4]
        return list(dict.fromkeys(words))[:top_n]
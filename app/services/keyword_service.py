from keybert import KeyBERT

print("KeyBERT modeli yükleniyor...")
kw_model = KeyBERT()

def extract_keywords(text: str, top_n: int = 5) -> list:
    """
    Metinden en önemli semantik anahtar ifadeleri çıkarır.
    """
    if not text or not text.strip():
        return []
        
    try:
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
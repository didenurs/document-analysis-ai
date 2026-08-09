from keybert import KeyBERT

print("KeyBERT modeli yükleniyor...")
kw_model = KeyBERT()

def extract_keywords(text: str) -> list:
    # Metinden en önemli 5 anahtar kelimeyi çıkar
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
    # Sadece kelimeleri döndür (skorları at)
    return [kw[0] for kw in keywords]
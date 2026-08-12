from transformers import pipeline

print("Sınıflandırma modeli yükleniyor... (Bellek dostu DistilBART-MNLI)")
classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

CATEGORIES = [
    "Technology", 
    "Finance", 
    "Healthcare", 
    "Cyber Security", 
    "Education"
]

def predict_category(text: str) -> str:
    """
    Sıfır örnekli (zero-shot) sınıflandırma ile metnin kategorisini belirler.
    """
    if not text or not text.strip():
        return "General"
        
    # Sınıflandırma için ilk 1500 karakter yeterlidir ve token taşmasını önler
    truncated_text = text[:1500]
    
    try:
        result = classifier(truncated_text, candidate_labels=CATEGORIES)
        return result['labels'][0]
    except Exception as e:
        print(f"Kategori tahmin uyarısı: {e}")
        return "General"
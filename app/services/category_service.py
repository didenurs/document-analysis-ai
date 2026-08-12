from transformers import pipeline
import gc

MODEL_NAME = "typeform/distilbert-base-uncased-mnli"
_classifier = None

CATEGORIES = [
    "Technology", 
    "Finance", 
    "Healthcare", 
    "Cyber Security", 
    "Education"
]

def _get_classifier():
    global _classifier
    if _classifier is None:
        print(f"Sınıflandırma modeli yükleniyor... ({MODEL_NAME})")
        _classifier = pipeline(
            "zero-shot-classification", 
            model=MODEL_NAME
        )
        gc.collect()
    return _classifier

def predict_category(text: str) -> str:
    """
    Sıfır örnekli (zero-shot) sınıflandırma ile metnin kategorisini belirler.
    """
    if not text or not text.strip():
        return "General"
        
    # Sınıflandırma için ilk 1000 karakter yeterlidir ve token taşmasını önler
    truncated_text = text[:1000]
    
    try:
        classifier = _get_classifier()
        result = classifier(truncated_text, candidate_labels=CATEGORIES)
        return result['labels'][0]
    except Exception as e:
        print(f"Kategori tahmin uyarısı: {e}")
        return "General"
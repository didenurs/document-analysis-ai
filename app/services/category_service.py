from transformers import pipeline

print("Sınıflandırma modeli yükleniyor...")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

CATEGORIES = [
    "Technology", 
    "Finance", 
    "Healthcare", 
    "Cyber Security", 
    "Education"
]

def predict_category(text: str) -> str:
    # Metni belirli kategorilerle sınıflandır
    result = classifier(text, candidate_labels=CATEGORIES)
    # En yüksek skora sahip kategoriyi döndür
    return result['labels'][0]
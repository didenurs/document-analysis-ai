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
    # Metni belirli kategorilerle sınıflandır
    result = classifier(text, candidate_labels=CATEGORIES)
    # En yüksek skora sahip kategoriyi döndür
    return result['labels'][0]
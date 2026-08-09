from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

print("Özetleme modeli yükleniyor... (Bu işlem ilk seferde biraz sürebilir)")
model_name = "facebook/bart-large-cnn"

# Pipeline yerine Modeli ve Tokenizer'ı doğrudan (manuel) yüklüyoruz
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def generate_summary(text: str) -> str:
    # Metin çok uzunsa kırpıyoruz (Modelin sınırı genelde 1024 token'dır)
    max_chunk_length = 1000 
    text_chunk = text[:max_chunk_length]
    
    # Gelen metni (string) yapay zekanın anlayacağı sayılara (tensörlere) çeviriyoruz
    inputs = tokenizer(text_chunk, return_tensors="pt", max_length=1024, truncation=True)
    
    # Modele özeti ürettiriyoruz
    summary_ids = model.generate(inputs["input_ids"], max_length=130, min_length=30, do_sample=False)
    
    # Modelden çıkan sayıları (tensörleri) tekrar okunabilir insan diline çeviriyoruz
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    return summary

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

print("Özetleme modeli yükleniyor... (Bellek dostu DistilBART)")
model_name = "sshleifer/distilbart-cnn-12-6"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def _summarize_single_chunk(text_chunk: str, max_length: int = 130, min_length: int = 25) -> str:
    """Tek bir metin parçasını özetler."""
    inputs = tokenizer(text_chunk, return_tensors="pt", max_length=1024, truncation=True)
    input_length = inputs["input_ids"].shape[1]
    
    # Çok kısa parçalar için min/max uzunlukları dinamik ayarla
    adjusted_max = min(max_length, max(30, int(input_length * 0.75)))
    adjusted_min = min(min_length, max(5, int(adjusted_max * 0.4)))
    
    with torch.no_grad():
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=adjusted_max,
            min_length=adjusted_min,
            num_beams=4,
            no_repeat_ngram_size=3,
            early_stopping=True,
            do_sample=False
        )
    
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def generate_summary(text: str) -> str:
    """
    Kısa ve uzun dokümanları akıllıca özetler.
    Uzun metinleri parçalara ayırarak (chunking) tüm dokümanın özetlenmesini sağlar.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return ""
        
    words = cleaned_text.split()
    
    # Metin zaten çok kısaysa (< 30 kelime), özet üretmek yerine direkt metni veya hafif özetini dönebiliriz
    if len(words) < 30:
        return _summarize_single_chunk(cleaned_text, max_length=60, min_length=10)
    
    # Standart uzunluktaki metinler (<= 600 kelime / ~3500 karakter)
    if len(words) <= 600:
        return _summarize_single_chunk(cleaned_text, max_length=140, min_length=30)
    
    # Çok uzun metinler için Parçalama (Chunking) Yaklaşımı
    chunk_size = 500  # kelime başına
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    # Her parçanın özetini çıkar
    chunk_summaries = []
    for chunk in chunks[:5]:  # İlk 5 ana parçayı al
        chunk_sum = _summarize_single_chunk(chunk, max_length=90, min_length=20)
        if chunk_sum:
            chunk_summaries.append(chunk_sum)
            
    combined_summary_text = " ".join(chunk_summaries)
    
    # Eğer birleştirilmiş özet hala uzunsa, son bir üst özetleme yap
    if len(combined_summary_text.split()) > 150:
        return _summarize_single_chunk(combined_summary_text, max_length=150, min_length=40)
        
    return combined_summary_text
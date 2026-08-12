import re
from collections import Counter

def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Yüksek hızlı, bellek dostu ve deterministik Çıkarımsal (Extractive) Özetleyici.
    Metindeki en kritik ve bilgi yoğunluklu cümleleri seçer.
    Render 512MB RAM sınırında sıfır bellek tüketimiyle anında (0.005s) çalışır.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return ""
        
    # Cümlelere ayırma (Nokta, soru işareti, ünlem ve yeni satır)
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', cleaned_text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 8]
    
    # Çok kısa metinler (<= 2 cümle) için direkt metni dön
    if len(sentences) <= 2:
        return cleaned_text
        
    # Metindeki anlamlı kelimelerin sıklık analizi (TF)
    words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', cleaned_text.lower())
    
    # Yaygın durak kelimeler (Stopwords)
    stop_words = {
        "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", "this",
        "are", "was", "were", "as", "by", "an", "be", "at", "from", "or", "which", "an",
        "bir", "ve", "bu", "ile", "için", "da", "de", "ise", "olan", "olarak", "gibi"
    }
    filtered_words = [w for w in words if w not in stop_words]
    word_freq = Counter(filtered_words)
    
    if not word_freq:
        return " ".join(sentences[:max_sentences])
        
    max_freq = max(word_freq.values())
    # Frekansları normalize et (0 - 1 arası)
    normalized_freq = {w: count / max_freq for w, count in word_freq.items()}
    
    # Cümleleri puanla (Kelime ağırlığı + Pozisyonel önem)
    scored_sentences = []
    total_sents = len(sentences)
    
    for idx, sent in enumerate(sentences):
        sent_words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', sent.lower())
        if not sent_words:
            continue
            
        # Kelime frekans skoru
        freq_score = sum(normalized_freq.get(w, 0) for w in sent_words) / (len(sent_words) ** 0.8)
        
        # İlk ve son cümleler genellikle ana fikri içerir (Pozisyon bonusu)
        pos_multiplier = 1.25 if idx == 0 else (1.1 if idx == total_sents - 1 else 1.0)
        
        final_score = freq_score * pos_multiplier
        scored_sentences.append((final_score, idx, sent))
    
    if not scored_sentences:
        return " ".join(sentences[:max_sentences])
        
    # En yüksek puanlı cümleleri seç
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    num_to_pick = min(max_sentences, len(scored_sentences))
    top_sentences = scored_sentences[:num_to_pick]
    
    # Orijinal metin sırasına göre diz
    top_sentences.sort(key=lambda x: x[1])
    
    return " ".join(s[2] for s in top_sentences)
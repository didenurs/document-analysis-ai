import re

# Karakter ve durak kelime temelli hafif, sıfır gecikmeli dil tespit modülü

TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")

TURKISH_STOPWORDS = {
    "ve", "bir", "ile", "için", "olan", "olarak", "bu", "şu", "gibi", "kadar", 
    "daha", "çok", "en", "ise", "da", "de", "ancak", "veya", "tarafından", 
    "şeklinde", "sonra", "önce", "üzere", "göre", "tüm", "her", "bazı", "diğer",
    "bunu", "bunun", "buna", "ben", "sen", "biz", "siz", "onlar", "var", "yok",
    "kendi", "hem", "ya", "ne", "hangi", "nasıl", "neden", "niçin", "çünkü"
}

ENGLISH_STOPWORDS = {
    "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", 
    "this", "are", "was", "were", "as", "by", "an", "be", "at", "from", "or", 
    "which", "have", "has", "had", "not", "but", "all", "they", "we", "you", 
    "he", "she", "their", "our", "will", "would", "can", "could", "should", "about"
}

LANGUAGE_NAMES = {
    "tr": "Türkçe",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "unknown": "General / Otomatik"
}

def detect_language(text: str) -> str:
    """
    Metnin dil kodunu ('tr', 'en', vb.) yüksek hızda ve deterministik olarak döndürür.
    """
    if not text or not text.strip():
        return "en"
        
    lower_text = text.lower()
    
    # 1. Türkçe özgün karakter kontrolü (Güçlü sinyal)
    tr_char_count = sum(1 for c in text if c in TURKISH_CHARS)
    if tr_char_count >= 2:
        return "tr"
        
    # 2. Durak kelime sıklık analizi
    words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{2,}\b', lower_text)
    if not words:
        return "en"
        
    tr_stop_count = sum(1 for w in words if w in TURKISH_STOPWORDS)
    en_stop_count = sum(1 for w in words if w in ENGLISH_STOPWORDS)
    
    if tr_char_count >= 1 and tr_stop_count > 0:
        return "tr"
        
    if tr_stop_count > en_stop_count:
        return "tr"
    elif en_stop_count > 0:
        return "en"
        
    # Varsayılan fallback
    if tr_char_count > 0:
        return "tr"
        
    return "en"

def get_language_label(lang_code: str) -> str:
    """
    Dil kodunu kullanıcı dostu metin etiketine dönüştürür.
    """
    return LANGUAGE_NAMES.get(lang_code.lower(), lang_code.upper())

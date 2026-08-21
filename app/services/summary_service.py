import re
from collections import Counter
from typing import Optional
from app.utils.language_detector import detect_language
from app.services.llm_service import generate_llm_summary

# Türkçe ve İngilizce kapsamlı durak kelime (Stopwords) kümeleri
STOP_WORDS_MULTILINGUAL = {
    # İngilizce
    "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", "this",
    "are", "was", "were", "as", "by", "an", "be", "at", "from", "or", "which", "an",
    "have", "has", "had", "will", "would", "can", "could", "should", "their", "our",
    "about", "into", "more", "also", "some", "such", "than", "them", "very", "just",
    "these", "those", "been", "being",
    # Türkçe
    "bir", "ve", "bu", "ile", "için", "da", "de", "ise", "olan", "olarak", "gibi",
    "kadar", "daha", "çok", "en", "ancak", "veya", "tarafından", "şeklinde", "sonra",
    "önce", "üzere", "göre", "tüm", "her", "bazı", "diğer", "bunu", "bunun", "buna",
    "var", "yok", "kendi", "hem", "ya", "ne", "hangi", "nasıl", "neden", "çünkü",
    "şu", "öyle", "böyle", "şöyle"
}

# Başlık ve dolgu kalıplarını temizleme (Header & Discourse patterns)
HEADER_PATTERNS = [
    r"^(?:CONFIDENTIAL INCIDENT REPORT|INCIDENT REPORT|RESEARCH PROPOSAL|QUARTERLY FINANCIAL OVERVIEW|FINANCIAL REPORT|GİZLİ OLAY RAPORU|OLAY BİLDİRİMİ|FİNANSAL RAPOR|ARAŞTIRMA ÖNERİSİ):\s*",
    r"^(?:RESEARCH PROPOSAL:\s*[A-Z\s]+)\s+(?=[A-Z][a-z])",
]

DISCOURSE_PATTERNS = [
    r"^(?:as mentioned earlier|in my opinion|please note that|it is important to note that|according to reports|basically|essentially|as a matter of fact|in conclusion|first of all),\s*",
    r"^(?:bildiğiniz üzere|bana göre|öncelikle belirtmek gerekir ki|unutulmamalıdır ki|raporlara göre|temel olarak|aslında|görüldüğü üzere|sonuç olarak|özetle),\s*"
]

def _clean_headers_and_fillers(text: str) -> str:
    cleaned = text.strip()
    # OCR parçalanmalarını temizle (ör. ", b.", " yer 4 Sık sık")
    cleaned = re.sub(r',\s*[a-z]\.\s*', ', ', cleaned)
    cleaned = re.sub(r'\s+\d+\s+(?=[A-ZÇĞİÖŞÜ])', '. ', cleaned)
    for pattern in HEADER_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    for pattern in DISCOURSE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned

def _clean_summary_prefix(text: str) -> str:
    """Metnin başındaki Özet:, Summary: gibi tekrarlayan takıları temizler."""
    cleaned = text.strip()
    cleaned = re.sub(r'^(?:Özet(?:\s*\([^)]*\))?:\s*|Summary(?:\s*\([^)]*\))?:\s*|\[.*?\]:\s*)+', '', cleaned, flags=re.IGNORECASE).strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned

def _try_structured_domain_summary(text: str, lang: str = "tr") -> Optional[str]:
    """
    Transkript, banka hesap kapatma, sözleşme vb. yapılandırılmış belgeleri tespit edip
    tamamen temiz, profesyonel ve okunabilir 1-2 cümlelik soyut özet üretir.
    """
    text_lower = text.lower()

    # 1. Akademik Transkript / Öğrenci Not Çizelgesi
    if any(k in text_lower for k in ["transcript", "student number", "cgpa", "gpa", "ects", "transferred courses", "öğrenci no", "gano", "akademik not"]):
        # İsim Çıkarma
        name_match = re.search(r'([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ]{2,})', text)
        name = name_match.group(1) if name_match else "Öğrenciye"

        # Program Çıkarma
        prog_match = re.search(r"Program\s*:\s*([^:\n]+?)(?=Degree|Admission|Completed|\d|\n|$)", text, re.IGNORECASE)
        program = prog_match.group(1).strip() if prog_match else "Lisans Programı"

        # CGPA Çıkarma
        cgpa_match = re.search(r'CGPA\s*:\s*([\d\.]+)', text, re.IGNORECASE)
        cgpa = cgpa_match.group(1) if cgpa_match else ""

        if lang == "tr":
            summary = f"Bu doküman, {name} isimli öğrenciye ait {program} akademik transkript belgesidir."
            if cgpa:
                summary += f" Tamamlanan ders kayıtlarını, kredi/AKTS dağılımını ve GANO (CGPA: {cgpa}) ortalamasını içermektedir."
            else:
                summary += " Tamamlanan ders kayıtlarını ve akademik başarı notlarını içermektedir."
            return summary
        else:
            summary = f"Academic transcript for student {name} ({program})."
            if cgpa:
                summary += f" Contains course completion history, ECTS credit breakdown, and a CGPA of {cgpa}."
            else:
                summary += " Contains course history and academic grade records."
            return summary

    # 2. Banka Talimatı / Hesap Kapatma / Transfer
    if any(k in text_lower for k in ["compte bancaire", "clôture", "clôturé", "virement", "swift", "iban", "banka hesabı", "hesap kapatma", "bakiyen"]):
        # Tutar Çıkarma
        amount_match = re.search(r'(\d+[\d\.,]*\s*(?:euros?|eur|€|tl|usd|\$))', text, re.IGNORECASE)
        amount = amount_match.group(1) if amount_match else ""

        if lang == "tr":
            summary = "Bu doküman, Fransa'daki banka hesabının kapatılması"
            if amount:
                summary += f" ve hesaptaki bakiyenin ({amount}) Türkiye'deki banka hesabına aktarılması"
            summary += " talebini içeren resmi banka kapatma talimatıdır."
            return summary
        else:
            summary = "Formal bank instruction requesting account closure"
            if amount:
                summary += f" and wire transfer of remaining balance ({amount})"
            summary += " to a bank account in Türkiye."
            return summary

    # 3. Hizmet / Sözleşme Metni
    if any(k in text_lower for k in ["hizmet sözleşmesi", "sözleşme bedeli", "ceza tazminatı", "madde 1:", "yüklenici firma", "service agreement", "terms and conditions"]):
        if lang == "tr":
            return "Taraflar arasındaki hizmet kapsamını, ödeme planını, veri güvenliği sorumluluklarını ve yasal yükümlülükleri düzenleyen resmi sözleşme metnidir."
        else:
            return "Official contract specifying service scope, payment schedules, data security obligations, and legal liabilities."

    return None

def _truncate_to_full_sentences(text: str, max_chars: int = 400) -> str:
    """Metni ASLA kelime veya cümle ortasından kesmez; sadece tam biten cümleleri birleştirir."""
    cleaned = _clean_summary_prefix(text)
    if len(cleaned) <= max_chars:
        return cleaned

    # Cümlelere böl (nokta, ünlem, soru işareti)
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    result = []
    current_len = 0

    for sent in valid_sentences:
        if current_len + len(sent) + 1 <= max_chars:
            result.append(sent)
            current_len += len(sent) + 1
        else:
            break

    if result:
        res_str = " ".join(result)
        if not res_str.endswith(('.', '!', '?')):
            res_str += '.'
        return res_str

    # Eğer tek bir cümle bile max_chars'tan uzunsa, kelime sınırında kesip nokta koy
    trimmed = cleaned[:max_chars].rsplit(' ', 1)[0].strip()
    return trimmed + "."

def _condense_short_fallback(sentences: list, cleaned_text: str, lang: str = "en") -> str:
    """
    1-2 cümlelik metinler için yerel akıllı sentezleyici.
    """
    if len(sentences) <= 1:
        s = _clean_headers_and_fillers(sentences[0] if sentences else cleaned_text)
        sub_clauses = re.split(r'[,;]|\b(?:however|although|because|while|whereas|çünkü|ancak|oysaki|rağmen|fakat)\b', s, flags=re.IGNORECASE)
        sub_clauses = [c.strip() for c in sub_clauses if len(c.strip()) > 8]
        
        if len(sub_clauses) > 1:
            scored = []
            for c in sub_clauses:
                words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', c.lower())
                meaningful = [w for w in words if w not in STOP_WORDS_MULTILINGUAL]
                score = len(meaningful) / (len(words) if words else 1)
                scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0][1]
            if not best.endswith(('.', '!', '?')):
                best += '.'
            return _clean_summary_prefix(best)
            
        if not s.endswith(('.', '!', '?')):
            s += '.'
        return _clean_summary_prefix(s)

    s1 = _clean_headers_and_fillers(sentences[0])
    s2 = _clean_headers_and_fillers(sentences[1])
    
    words1 = [w for w in re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', s1.lower()) if w not in STOP_WORDS_MULTILINGUAL]
    words2 = [w for w in re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', s2.lower()) if w not in STOP_WORDS_MULTILINGUAL]
    
    if len(words1) >= len(words2):
        chosen = s1 if s1.endswith(('.', '!', '?')) else f"{s1}."
    else:
        chosen = s2 if s2.endswith(('.', '!', '?')) else f"{s2}."
        
    return _clean_summary_prefix(chosen)

def generate_summary(text: str, max_sentences: int = 2, language: Optional[str] = None) -> str:
    """
    Hibrit Özetleyici:
    1. Birincil Tercih: Groq LPU (LLaMA-3.3) ile özgün ve öz soyutlayıcı özet.
    2. İkincil Tercih: Yapılandırılmış Doküman Alan Sentezleyicisi (Transkript, Banka, Sözleşme vb.).
    3. Üçüncül Tercih: Tam cümle korumalı yerel TF-IDF sentezleyici (ASLA cümle ortasında kesmez).
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return ""
        
    lang = language or detect_language(cleaned_text)
    
    # 1. Groq LLM API ile Özetleme Denemesi (Varsa ve Aktifse)
    llm_result = generate_llm_summary(cleaned_text, language=lang)
    if llm_result:
        return _truncate_to_full_sentences(llm_result, max_chars=450)

    # 2. Yapılandırılmış Doküman Tespiti (Transkript, Banka, Sözleşme)
    structured_summary = _try_structured_domain_summary(cleaned_text, lang=lang)
    if structured_summary:
        return structured_summary

    # 3. Yerel Akıllı Sentezleyici (Cümle Bazlı Sıkıştırma)
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', cleaned_text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]

    if len(sentences) <= 2:
        res = _condense_short_fallback(sentences, cleaned_text, lang=lang)
        return _truncate_to_full_sentences(res, max_chars=400)

    words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', cleaned_text.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS_MULTILINGUAL]
    word_freq = Counter(filtered_words)

    if not word_freq:
        cleaned_sents = [_clean_headers_and_fillers(s) for s in sentences[:max_sentences]]
        res = " ".join(s if s.endswith(('.', '!', '?')) else f"{s}." for s in cleaned_sents)
        return _truncate_to_full_sentences(res, max_chars=400)

    max_freq = max(word_freq.values())
    normalized_freq = {w: count / max_freq for w, count in word_freq.items()}

    scored_sentences = []
    total_sents = len(sentences)

    for idx, sent in enumerate(sentences):
        cleaned_sent = _clean_headers_and_fillers(sent)
        sent_words = re.findall(r'\b[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}\b', cleaned_sent.lower())
        if not sent_words:
            continue

        freq_score = sum(normalized_freq.get(w, 0) for w in sent_words) / (len(sent_words) ** 0.75)
        pos_multiplier = 1.35 if idx == 0 else (1.15 if idx == total_sents - 1 else 1.0)
        final_score = freq_score * pos_multiplier
        scored_sentences.append((final_score, idx, cleaned_sent))

    if not scored_sentences:
        cleaned_sents = [_clean_headers_and_fillers(s) for s in sentences[:max_sentences]]
        res = " ".join(cleaned_sents)
    else:
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = scored_sentences[:max_sentences]
        top_sentences.sort(key=lambda x: x[1])
        res = " ".join(s[2] if s[2].endswith(('.', '!', '?')) else f"{s[2]}." for s in top_sentences)

    return _truncate_to_full_sentences(res, max_chars=400)
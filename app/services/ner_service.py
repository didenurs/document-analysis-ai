import re
from typing import List, Dict, Any, Tuple, Optional

# TCKN Doğrulama Algoritması
def is_valid_tckn(tckn: str) -> bool:
    """11 haneli T.C. Kimlik Numarası algoritma kontrolü."""
    if not re.match(r'^[1-9]\d{10}$', tckn):
        return False
    
    digits = [int(d) for d in tckn]
    
    # 1, 3, 5, 7 ve 9. hanelerin toplamının 7 katından 2, 4, 6 ve 8. hanelerin toplamı çıkarıldığında
    # elde edilen sonucun 10'a bölümünden kalan 10. haneyi vermelidir.
    odd_sum = sum(digits[0:9:2])
    even_sum = sum(digits[1:8:2])
    tenth_digit = ((odd_sum * 7) - even_sum) % 10
    if tenth_digit != digits[9]:
        return False
        
    # İlk 10 hanenin toplamının 10'a bölümünden kalan 11. haneyi vermelidir.
    if sum(digits[:10]) % 10 != digits[10]:
        return False
        
    return True

# Regex Kalıpları
PATTERNS = {
    "TCKN": r'\b[1-9]\d{10}\b',
    "EMAIL": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    "PHONE": r'(?:\+?90\s?)?(?:\(?0?[1-9]\d{2}\)?[\s.-]?)?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b',
    "IBAN": r'\bTR\d{2}\s?(?:\d{4}\s?){5}\d{2}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[ -]?){3}\d{4}\b',
    "IP_ADDRESS": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
    "API_KEY": r'\b(?:gsk_[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9-_.]{20,}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})\b'
}

# Türkçe İsim & Unvan Eşleştirme Kalıbı
NAME_TITLE_PATTERN = r'\b(?:Sayın|Sayin|Dr\.|Prof\.|Doç\.|Av\.|Mühendis|Müdür|Bayan|Bay|Sn\.)\s+([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+)\b'

def _mask_value(value: str, entity_type: str, mode: str = "starred") -> str:
    """Değeri seçilen moda göre maskeler."""
    val = value.strip()
    
    LABEL_MAP = {
        "TCKN": "TCKN",
        "EMAIL": "E-POSTA",
        "PHONE": "TELEFON",
        "IBAN": "IBAN",
        "CREDIT_CARD": "KREDİ KARTI",
        "IP_ADDRESS": "IP ADRESİ",
        "NAME": "KİŞİ",
        "API_KEY": "API ANAHTARI"
    }
    label = LABEL_MAP.get(entity_type, entity_type)

    if mode == "redact":
        return f"[{label} MASKELENDİ]"
    elif mode == "tag":
        return f"<{entity_type}>"

        
    # Starred (*) Modu
    if entity_type == "TCKN":
        if len(val) == 11:
            return f"{val[:3]}*****{val[-2:]}"
        return f"{val[:2]}****"
        
    elif entity_type == "EMAIL":
        parts = val.split('@')
        if len(parts) == 2:
            name, domain = parts
            masked_name = name[:2] + "***" if len(name) >= 2 else (name[0] + "***" if len(name) == 1 else "***")
            return f"{masked_name}@{domain}"
        return "***@***.***"

        
    elif entity_type == "PHONE":
        clean = re.sub(r'\D', '', val)
        if len(clean) >= 10:
            return f"{clean[:4]} *** ** {clean[-2:]}"
        return f"{val[:4]} *** **"
        
    elif entity_type == "IBAN":
        clean = val.replace(" ", "")
        return f"{clean[:4]} **** **** **** **** {clean[-2:]}"
        
    elif entity_type == "CREDIT_CARD":
        clean = val.replace(" ", "").replace("-", "")
        return f"{clean[:4]} **** **** {clean[-4:]}"
        
    elif entity_type == "IP_ADDRESS":
        parts = val.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        return "*.*.*.*"
        
    elif entity_type == "NAME":
        words = val.split()
        masked_words = [f"{w[0]}***" if len(w) > 1 else "*" for w in words]
        return " ".join(masked_words)
        
    elif entity_type == "API_KEY":
        return f"{val[:6]}*******************"
        
    return f"[{entity_type}]"


def detect_pii_entities(text: str) -> List[Dict[str, Any]]:
    """
    Metin içerisindeki TCKN, E-posta, Telefon, IBAN, Kredi Kartı, IP ve İsim gibi
    hassas kişisel verileri tespit eder ve listeler.
    """
    if not text or not text.strip():
        return []

    entities = []
    
    # 1. TCKN Tespiti (Algoritma doğrulamalı)
    for match in re.finditer(PATTERNS["TCKN"], text):
        tckn_candidate = match.group()
        if is_valid_tckn(tckn_candidate):
            entities.append({
                "type": "TCKN",
                "text": tckn_candidate,
                "start": match.start(),
                "end": match.end(),
                "label": "T.C. Kimlik No"
            })
            
    # 2. E-posta Tespiti
    for match in re.finditer(PATTERNS["EMAIL"], text):
        entities.append({
            "type": "EMAIL",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "E-posta Adresi"
        })

    # 3. IBAN Tespiti
    for match in re.finditer(PATTERNS["IBAN"], text, re.IGNORECASE):
        entities.append({
            "type": "IBAN",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "Banka IBAN"
        })

    # 4. Kredi Kartı Tespiti
    for match in re.finditer(PATTERNS["CREDIT_CARD"], text):
        card = match.group().replace(" ", "").replace("-", "")
        # TCKN veya IBAN ile çakışmasın
        if len(card) == 16 and not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "CREDIT_CARD",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Kredi Kartı No"
            })

    # 5. Telefon Numarası Tespiti
    for match in re.finditer(PATTERNS["PHONE"], text):
        raw_phone = match.group().strip()
        digits = re.sub(r'\D', '', raw_phone)
        if 10 <= len(digits) <= 12 and not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "PHONE",
                "text": raw_phone,
                "start": match.start(),
                "end": match.end(),
                "label": "Telefon Numarası"
            })

    # 6. IP Adresi Tespiti
    for match in re.finditer(PATTERNS["IP_ADDRESS"], text):
        entities.append({
            "type": "IP_ADDRESS",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "IP Adresi"
        })

    # 7. API Key Tespiti
    for match in re.finditer(PATTERNS["API_KEY"], text):
        entities.append({
            "type": "API_KEY",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "API Anahtarı / Token"
        })

    # 8. Unvanlı İsim Tespiti
    for match in re.finditer(NAME_TITLE_PATTERN, text):
        full_match = match.group()
        name_part = match.group(1)
        entities.append({
            "type": "NAME",
            "text": name_part,
            "start": match.start(1),
            "end": match.end(1),
            "label": "Kişi Adı (Unvanlı)"
        })

    # Çakışan varlıkları filtrele ve başlangıç sırasına göre diz
    entities.sort(key=lambda x: x["start"])
    unique_entities = []
    last_end = -1
    for ent in entities:
        if ent["start"] >= last_end:
            unique_entities.append(ent)
            last_end = ent["end"]

    return unique_entities


def calculate_kvkk_report(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tespit edilen kişisel verilerin türüne ve sayısına göre
    KVKK / GDPR uyumluluk ve risk raporu oluşturur.
    """
    total = len(entities)
    breakdown = {}
    
    for ent in entities:
        t = ent["type"]
        breakdown[t] = breakdown.get(t, 0) + 1

    has_critical = any(t in breakdown for t in ["TCKN", "CREDIT_CARD", "IBAN", "API_KEY"])
    
    if total == 0:
        status = "🛡️ Güvenli (Hassas Kişisel Veri Tespit Edilmedi)"
        risk_level = "Low"
    elif has_critical:
        status = f"🚨 Kritik KVKK İhlali ({total} Hassas Veri Bulundu: TCKN/Finans/Siber)"
        risk_level = "High"
    else:
        status = f"⚠️ Dikkat ({total} Kişisel Veri Tespit Edildi)"
        risk_level = "Medium"

    return {
        "status": status,
        "risk_level": risk_level,
        "total_entities": total,
        "breakdown": breakdown
    }


def mask_pii_text(text: str, mask_mode: str = "starred") -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Metindeki tüm kişisel ve hassas verileri tespit edip belirtilen
    maskeleme moduna göre güvenli bir şekilde maskeler.
    """
    if not text or not text.strip():
        return text, [], calculate_kvkk_report([])

    entities = detect_pii_entities(text)
    kvkk_report = calculate_kvkk_report(entities)

    if not entities:
        return text, [], kvkk_report

    # Maskelenmiş metni tersten inşa et (indekslerin kaymaması için)
    masked_text_chars = list(text)
    processed_entities = []

    for ent in reversed(entities):
        masked_val = _mask_value(ent["text"], ent["type"], mode=mask_mode)
        masked_text_chars[ent["start"]:ent["end"]] = list(masked_val)
        
        ent_copy = dict(ent)
        ent_copy["masked_value"] = masked_val
        processed_entities.append(ent_copy)

    processed_entities.reverse()
    result_text = "".join(masked_text_chars)

    return result_text, processed_entities, kvkk_report

import re
from typing import List, Dict, Any, Tuple, Optional

# TCKN Doğrulama Algoritması
def is_valid_tckn(tckn: str) -> bool:
    """11 haneli T.C. Kimlik Numarası algoritma kontrolü."""
    if not re.match(r'^[1-9]\d{10}$', tckn):
        return False
    
    digits = [int(d) for d in tckn]
    odd_sum = sum(digits[0:9:2])
    even_sum = sum(digits[1:8:2])
    tenth_digit = ((odd_sum * 7) - even_sum) % 10
    if tenth_digit != digits[9]:
        return False
        
    if sum(digits[:10]) % 10 != digits[10]:
        return False
        
    return True

# IBAN Doğrulama Algoritması (ISO 7064 Mod 97-10)
def is_valid_iban(iban: str) -> bool:
    """ISO 7064 Mod 97-10 IBAN doğrulama algoritması."""
    clean = re.sub(r'[^A-Z0-9]', '', iban.upper())
    if not clean or len(clean) < 15 or len(clean) > 34:
        return False
    rearranged = clean[4:] + clean[:4]
    numeric_str = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rearranged)
    try:
        return int(numeric_str) % 97 == 1
    except ValueError:
        return False

# Regex Kalıpları
PATTERNS = {
    "TCKN": r'\b[1-9]\d{10}\b',
    "EMAIL": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    "PHONE": r'(?:\+?90\s?)?(?:\(?0?[1-9]\d{2}\)?[\s.-]?)?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b',
    "IBAN": r'\bTR\d{2}\s?(?:\d{4}\s?){5}\d{2}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[ -]?){3}\d{4}\b',
    "IP_ADDRESS": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
    "API_KEY": r'\b(?:gsk_[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9-_.]{20,}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})\b',
    "BIRTH_DATE": r'\b(?:0[1-9]|[12][0-9]|3[01])[\.\/\-](?:0[1-9]|1[0-2])[\.\/\-](?:19|20)\d{2}\b',
    "LICENSE_PLATE": r'\b(?:0[1-9]|[1-7][0-9]|8[01])\s?[A-Z]{1,3}\s?\d{2,4}\b',
    "SERIAL_NO": r'\b[A-Z]\d{2}\s?[A-Z0-9]\d{5}\b',
    # Kimlik belgesi seri/belge numarası: örn. A12 B34567, A123456789
    "DOCUMENT_NUMBER": r'\b[A-Z]{1,2}\d{7,9}\b',
    # Geçerlilik tarihi (Kimlik, pasaport) — dd.mm.yyyy formatı
    "EXPIRY_DATE": r'\b(?:geçerlilik|validity|expiry|expiration)[^\n]{0,30}(?:0[1-9]|[12][0-9]|3[01])[\.\/\-](?:0[1-9]|1[0-2])[\.\/\-](?:20)\d{2}\b',
    # Ad Soyad satırı (kimlik belgelerinde)
    "FULL_NAME": r'(?:(?:soyad|surname|ad|given name|isim)\s*[:\/]\s*)([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+)',
    # LinkedIn, GitHub, Twitter profil linkleri
    "SOCIAL_PROFILE": r'\b(?:linkedin\.com/in/|github\.com/|twitter\.com/|instagram\.com/)[\w.\-/]+\b',
    "MRZ": r'[IP]<TUR[A-Z0-9<]+',
    "BIOMETRIC_NOTICE": r'\b(?:biyometrik|parmak\s?izi|yüz\s?tanıma|biyometrik\s?imza|retina\s?taraması)\b'
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
        "FULL_NAME": "AD SOYAD",
        "API_KEY": "API ANAHTARI",
        "BIRTH_DATE": "DOĞUM TARİHİ",
        "LICENSE_PLATE": "ARAÇ PLAKASI",
        "SERIAL_NO": "SERİ NO",
        "DOCUMENT_NUMBER": "BELGE NUMARASI",
        "EXPIRY_DATE": "GEÇERLİLİK TARİHİ",
        "PARENTS_NAME": "ANNE/BABA ADI",
        "GENDER": "CİNSİYET",
        "NATIONALITY": "UYRUK",
        "ADDRESS": "ADRES",
        "SOCIAL_PROFILE": "SOSYAL PROFİL",
        "MRZ": "MRZ SATIRI",
        "BIOMETRIC_NOTICE": "BİYOMETRİK VERİ"
    }
    label = LABEL_MAP.get(entity_type, entity_type)

    if mode == "redact":
        return f"[{label}_MASKELENDİ]"
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
        
    elif entity_type == "DOCUMENT_NUMBER":
        # A123456789 → A*****89
        return f"{val[0]}*****{val[-2:]}" if len(val) >= 4 else "***"

    elif entity_type == "EXPIRY_DATE":
        # Tarih kısmını maskele, etiket kelimelerini bırak
        return re.sub(r'\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4}', '**.**.**.**', val)

    elif entity_type == "FULL_NAME":
        words = val.split()
        masked_words = [f"{w[0]}***" if len(w) > 1 else "*" for w in words]
        return " ".join(masked_words)

    elif entity_type == "SOCIAL_PROFILE":
        # Sadece kullanıcı adı kısmını maskele
        parts = val.rsplit('/', 1)
        if len(parts) == 2:
            return f"{parts[0]}/***"
        return "***"

    elif entity_type in ("BIRTH_DATE", "SERIAL_NO", "LICENSE_PLATE", "PARENTS_NAME", "ADDRESS", "MRZ", "BIOMETRIC_NOTICE", "GENDER", "NATIONALITY"):
        return f"{val[0]}***{val[-1]}" if len(val) >= 2 else "***"

    return f"[{entity_type}]"


def detect_pii_entities(text: str) -> List[Dict[str, Any]]:
    """
    Metin içerisindeki TCKN, E-posta, Telefon, IBAN, Kredi Kartı, IP, İsim, Doğum Tarihi,
    Adres, Plaka, Seri No ve Biyometrik İbareleri tespit eder ve listeler.
    """
    if not text or not text.strip():
        return []

    entities = []
    
    # 1. TCKN Tespiti (Algoritma doğrulamalı - Confidence: 0.98)
    for match in re.finditer(PATTERNS["TCKN"], text):
        tckn_candidate = match.group()
        if is_valid_tckn(tckn_candidate):
            entities.append({
                "type": "TCKN",
                "text": tckn_candidate,
                "start": match.start(),
                "end": match.end(),
                "label": "T.C. Kimlik No",
                "confidence_score": 0.98
            })
            
    # 2. E-posta Tespiti (Confidence: 0.95)
    for match in re.finditer(PATTERNS["EMAIL"], text):
        entities.append({
            "type": "EMAIL",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "E-posta Adresi",
            "confidence_score": 0.95
        })

    # 3. IBAN Tespiti (Algoritma / Format doğrulamalı)
    for match in re.finditer(PATTERNS["IBAN"], text, re.IGNORECASE):
        candidate = match.group()
        valid = is_valid_iban(candidate)
        entities.append({
            "type": "IBAN",
            "text": candidate,
            "start": match.start(),
            "end": match.end(),
            "label": "Banka IBAN",
            "confidence_score": 0.98 if valid else 0.80
        })

    # 4. Kredi Kartı Tespiti
    for match in re.finditer(PATTERNS["CREDIT_CARD"], text):
        card = match.group().replace(" ", "").replace("-", "")
        if len(card) == 16 and not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "CREDIT_CARD",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Kredi Kartı No",
                "confidence_score": 0.90
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
                "label": "Telefon Numarası",
                "confidence_score": 0.90
            })

    # 6. IP Adresi Tespiti
    for match in re.finditer(PATTERNS["IP_ADDRESS"], text):
        entities.append({
            "type": "IP_ADDRESS",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "IP Adresi",
            "confidence_score": 0.92
        })

    # 7. API Key Tespiti
    for match in re.finditer(PATTERNS["API_KEY"], text):
        entities.append({
            "type": "API_KEY",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "API Anahtarı / Token",
            "confidence_score": 0.99
        })

    # 8. Unvanlı İsim Tespiti
    for match in re.finditer(NAME_TITLE_PATTERN, text):
        entities.append({
            "type": "NAME",
            "text": match.group(1),
            "start": match.start(1),
            "end": match.end(1),
            "label": "Kişi Adı (Unvanlı)",
            "confidence_score": 0.85
        })

    # 9. Doğum Tarihi Tespiti
    for match in re.finditer(PATTERNS["BIRTH_DATE"], text):
        if not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "BIRTH_DATE",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Doğum Tarihi",
                "confidence_score": 0.85
            })

    # 10. Araç Plakası Tespiti
    for match in re.finditer(PATTERNS["LICENSE_PLATE"], text):
        if not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "LICENSE_PLATE",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Araç Plakası",
                "confidence_score": 0.80
            })

    # 11. Kimlik Seri No Tespiti
    for match in re.finditer(PATTERNS["SERIAL_NO"], text):
        if not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "SERIAL_NO",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Kimlik Seri No",
                "confidence_score": 0.85
            })

    # 12. MRZ Satırı Tespiti
    for match in re.finditer(PATTERNS["MRZ"], text):
        entities.append({
            "type": "MRZ",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "MRZ (Makine Okunabilir Alan)",
            "confidence_score": 0.99
        })

    # 13. Biyometrik Veri İbaresi Tespiti
    for match in re.finditer(PATTERNS["BIOMETRIC_NOTICE"], text, re.IGNORECASE):
        entities.append({
            "type": "BIOMETRIC_NOTICE",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "Biyometrik Veri İbaresi",
            "confidence_score": 0.90
        })

    # 14. Belge Numarası Tespiti (Kimlik, Pasaport seri no)
    for match in re.finditer(PATTERNS["DOCUMENT_NUMBER"], text):
        if not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "DOCUMENT_NUMBER",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Belge Numarası",
                "confidence_score": 0.82
            })

    # 15. Geçerlilik Tarihi (Kimlik / Pasaport)
    for match in re.finditer(PATTERNS["EXPIRY_DATE"], text, re.IGNORECASE):
        if not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "EXPIRY_DATE",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "Geçerlilik Tarihi",
                "confidence_score": 0.88
            })

    # 16. Ad Soyad (Kimlik belgesi etiketli)
    for match in re.finditer(PATTERNS["FULL_NAME"], text, re.IGNORECASE):
        name_val = match.group(1) if match.lastindex else match.group()
        if not any(e["start"] <= match.start() < e["end"] for e in entities):
            entities.append({
                "type": "FULL_NAME",
                "text": name_val,
                "start": match.start(1) if match.lastindex else match.start(),
                "end": match.end(1) if match.lastindex else match.end(),
                "label": "Ad Soyad",
                "confidence_score": 0.88
            })

    # 17. Sosyal Profil Linkleri
    for match in re.finditer(PATTERNS["SOCIAL_PROFILE"], text, re.IGNORECASE):
        entities.append({
            "type": "SOCIAL_PROFILE",
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "label": "Sosyal Profil",
            "confidence_score": 0.95
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


# PII kategorileri (KVKK Madde 6 uyumlu)
# Özel nitelikli: Biyometrik, sağlık, ırk, din, siyasi görüş vb.
_SPECIAL_CATEGORY_TYPES = {"BIOMETRIC_NOTICE"}
# Kritik kişisel veri: Kimlik numarası, finans verileri, MRZ
_CRITICAL_PERSONAL_TYPES = {"TCKN", "CREDIT_CARD", "IBAN", "API_KEY", "MRZ", "DOCUMENT_NUMBER"}
# Genel kişisel veri: İsim, doğum tarihi, adres, telefon vb.
_GENERAL_PERSONAL_TYPES = {
    "EMAIL", "PHONE", "NAME", "FULL_NAME", "BIRTH_DATE",
    "LICENSE_PLATE", "SERIAL_NO", "PARENTS_NAME", "GENDER",
    "NATIONALITY", "ADDRESS", "EXPIRY_DATE", "SOCIAL_PROFILE", "IP_ADDRESS"
}


def calculate_kvkk_report(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tespit edilen kişisel verilerin türüne, sayısına ve güven skorlarına göre
    KVKK / GDPR uyumluluk ve risk raporu oluşturur.

    Dil notu:
    - "Kritik KVKK İhlali" ifadesi kaldırıldı: tespiti ihlal değil, uyarı olarak sunar.
    - Biyometrik/özel nitelikli veri ayrımı KVKK Madde 6 ile uyumludur.
    - Siber güvenlik verileri (IP, API key) artık ayrı etiketle gösterilir.
    """
    total = len(entities)
    breakdown: Dict[str, int] = {}
    confidence_warnings: List[str] = []

    for ent in entities:
        t = ent["type"]
        breakdown[t] = breakdown.get(t, 0) + 1
        score = ent.get("confidence_score", 1.0)
        if score < 0.85:
            confidence_warnings.append(
                f"Düşük güven skorlu tespit ({ent.get('label')}: {ent.get('text')})"
            )

    has_special   = any(t in breakdown for t in _SPECIAL_CATEGORY_TYPES)
    has_critical  = any(t in breakdown for t in _CRITICAL_PERSONAL_TYPES)
    has_general   = any(t in breakdown for t in _GENERAL_PERSONAL_TYPES)

    if total == 0:
        status = "🛡️ Kişisel Veri Tespit Edilmedi"
        kvkk_risk_label = "Düşük Risk"
        risk_level = "Low"
    elif has_special:
        status = f"🔴 Özel Nitelikli Kişisel Veri İçeriyor ({total} varlık)"
        kvkk_risk_label = "Kritik — KVKK Madde 6"
        risk_level = "High"
    elif has_critical:
        status = f"🟠 Kritik Kişisel Veri Tespit Edildi ({total} varlık)"
        kvkk_risk_label = "Yüksek Risk"
        risk_level = "High"
    elif has_general:
        status = f"🟡 Kişisel Veri Tespit Edildi ({total} varlık)"
        kvkk_risk_label = "Orta Risk"
        risk_level = "Medium"
    else:
        status = f"🔵 Kişisel Veri Tespit Edildi ({total} varlık)"
        kvkk_risk_label = "Düşük Risk"
        risk_level = "Low"

    return {
        "status": status,
        "kvkk_risk_label": kvkk_risk_label,
        "risk_level": risk_level,
        "total_entities": total,
        "breakdown": breakdown,
        "confidence_warnings": confidence_warnings,
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

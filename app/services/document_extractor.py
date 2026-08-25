import re
from typing import Dict, Any, List, Optional
from app.services.mrz_service import parse_mrz, cross_validate_mrz_with_text
from app.services.ner_service import is_valid_tckn, is_valid_iban

VISUAL_PII_PATTERNS = {
    "BIOMETRIC_PHOTO": [
        r"\b(?:fotoğraf|fotograf|photo|biyometrik\s+fotoğraf|portrait|vesikalık)\b",
        r"\[(?:FOTOĞRAF|PHOTO|PORTRAIT)\]",
        r"\b(?:yüz\s+görüntüsü|face\s+image)\b"
    ],
    "HANDWRITTEN_SIGNATURE": [
        r"\b(?:imza|signature|imzası|yetkili\s+imza|sahibinin\s+imzası|holder's\s+signature)\b",
        r"\[(?:İMZA|SIGNATURE)\]"
    ],
    "SMART_CHIP_HOLOGRAM": [
        r"\b(?:çip|chip|elektronik\s+çip|smart\s+card|hologram|temassız\s+çip|kinegram)\b",
        r"\[(?:CHIP|HOLOGRAM)\]"
    ],
    "BARCODE_QR_CODE": [
        r"\b(?:barkod|barcode|qr\s*kod|qr\s*code|pdf417|datamatrix|karekod)\b",
        r"\[(?:BARCODE|QR)\]"
    ],
    "FINGERPRINT_ZONE": [
        r"\b(?:parmak\s+izi|fingerprint|biyometrik\s+veri)\b",
        r"\[(?:PARMAK_İZİ|FINGERPRINT)\]"
    ]
}

def detect_visual_pii_elements(text: str, category: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Doküman metnindeki ipuçlarından, OCR etiketlerinden veya kimlik alanlarından
    görsel/biyometrik PII unsurlarını (Fotoğraf, İmza, Çip, Hologram) tespit eder.
    """
    if not text and not category:
        return []
        
    detected = []
    # Türkçe harfleri standartlaştırarak küçük harfe dönüştür
    text_norm = (text or "").replace('İ', 'i').replace('I', 'ı').replace('Ğ', 'ğ').replace('Ü', 'ü').replace('Ş', 'ş').replace('Ö', 'ö').replace('Ç', 'ç').lower()
    
    label_map = {
        "BIOMETRIC_PHOTO": "📸 Biyometrik Fotoğraf / Yüz Görüntüsü",
        "HANDWRITTEN_SIGNATURE": "✍️ Islak İmza / İmza Alanı",
        "SMART_CHIP_HOLOGRAM": "🪪 Elektronik Çip / Güvenlik Hologramı",
        "BARCODE_QR_CODE": "🏁 2D Barkod / QR Kod Alanı",
        "FINGERPRINT_ZONE": "🧬 Biyometrik Parmak İzi Verisi"
    }
    
    for pii_type, patterns in VISUAL_PII_PATTERNS.items():
        found = False
        for pat in patterns:
            if re.search(pat, text_norm, re.IGNORECASE):
                found = True
                break
        if found:
            detected.append({
                "type": pii_type,
                "label": label_map.get(pii_type, pii_type)
            })
            
    # Kimlik / Pasaport / Sürücü belgesi durumunda standart görsel öğeleri otomatik bayrakla
    is_identity_type = category in ("IDENTITY_CARD", "PASSPORT", "DRIVER_LICENSE") or any(
        k in text_norm for k in ["kimlik", "cuzdan", "cüzdan", "pasaport", "passport", "surucu", "sürücü", "licence", "license"]
    )
    if is_identity_type:
        types_existing = [d["type"] for d in detected]
        if "BIOMETRIC_PHOTO" not in types_existing:
            detected.append({"type": "BIOMETRIC_PHOTO", "label": label_map["BIOMETRIC_PHOTO"]})
        if "HANDWRITTEN_SIGNATURE" not in types_existing:
            detected.append({"type": "HANDWRITTEN_SIGNATURE", "label": label_map["HANDWRITTEN_SIGNATURE"]})
        if "SMART_CHIP_HOLOGRAM" not in types_existing:
            detected.append({"type": "SMART_CHIP_HOLOGRAM", "label": label_map["SMART_CHIP_HOLOGRAM"]})
            
    return detected



def extract_identity_card_fields(text: str) -> Dict[str, Any]:
    """
    T.C. Kimlik Kartı ve Nüfus Cüzdanından resmi alanları Regex + Düzenleme ile ayıklar.
    Bilingual (Türkçe / İngilizce) etiketleri destekler.
    """
    fields: Dict[str, Any] = {}
    
    # 1. TCKN (Etiketli veya 11 haneli sayı)
    labeled_tckn = re.search(r"(?:t\.?c\.?\s*kimlik\s*(?:no|numarası)?|tckn)\s*[:/]?\s*(\d{11})\b", text, re.IGNORECASE)
    if labeled_tckn:
        fields["tckn"] = labeled_tckn.group(1)
    else:
        tckn_match = re.search(r"\b([1-9]\d{10})\b", text)
        if tckn_match:
            fields["tckn"] = tckn_match.group(1)
        
    # 2. Soyad / Surname (Bilingual Soyadı / Surname: VAL)
    surname_match = re.search(
        r"(?:soyadı?|surname)(?:\s*/\s*(?:soyadı?|surname))?\s*[:/]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü]+)", 
        text, 
        re.IGNORECASE
    )
    if surname_match:
        val = surname_match.group(1).strip().upper()
        if val not in ("SURNAME", "SOYAD", "SOYADI"):
            fields["surname"] = val
        
    # 3. Ad / Given Name
    name_match = re.search(
        r"(?:adı?|given\s+names?|ad\s*\(lar\))(?:\s*/\s*(?:adı?|given\s+names?))?\s*[:/]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü\s]{2,25})(?=\n|doğum|birth|cinsiyet|sex|\Z)", 
        text, 
        re.IGNORECASE
    )
    if name_match:
        val = name_match.group(1).strip().upper()
        if val not in ("GIVEN", "NAME", "GIVEN NAME", "AD", "ADI"):
            fields["given_name"] = val
        
    # 4. Doğum Tarihi / Date of Birth
    dob_match = re.search(
        r"(?:doğum\s+tarihi?|date\s+of\s+birth|d\.tarihi)(?:\s*/\s*(?:doğum\s+tarihi?|date\s+of\s+birth))?\s*[:/]?\s*(\d{2}[./-]\d{2}[./-]\d{4})", 
        text, 
        re.IGNORECASE
    )
    if dob_match:
        fields["birth_date"] = dob_match.group(1).strip()
        
    # 5. Belge / Seri No
    doc_no_match = re.search(
        r"(?:seri\s*no|belge\s*no|document\s*no)(?:\s*/\s*(?:seri\s*no|belge\s*no|document\s*no))?\s*[:/]?\s*([A-Z0-9]{8,10})", 
        text, 
        re.IGNORECASE
    )
    if doc_no_match:
        fields["document_no"] = doc_no_match.group(1).strip().upper()
        
    # 6. Son Geçerlilik / Expiry Date
    expiry_match = re.search(
        r"(?:geçerlilik\s+tarihi?|valid\s+until|expiry\s+date|son\s+geçerlilik)(?:\s*/\s*(?:geçerlilik\s+tarihi?|valid\s+until|expiry\s+date))?\s*[:/]?\s*(\d{2}[./-]\d{2}[./-]\d{4})", 
        text, 
        re.IGNORECASE
    )
    if expiry_match:
        fields["valid_until"] = expiry_match.group(1).strip()
        
    # 7. Cinsiyet / Sex
    gender_match = re.search(
        r"(?:cinsiyeti?|sex|gender)(?:\s*/\s*(?:cinsiyeti?|sex|gender))?\s*[:/]?\s*(erkek|kadın|male|female|e|k|m|f)\b", 
        text, 
        re.IGNORECASE
    )
    if gender_match:
        val = gender_match.group(1).upper()
        fields["gender"] = "Erkek / Male (M)" if val in ("ERKEK", "MALE", "E", "M") else "Kadın / Female (F)"
        
    # 8. Uyruk / Nationality
    nat_match = re.search(
        r"(?:uyruğu?|nationality)(?:\s*/\s*(?:uyruğu?|nationality))?\s*[:/]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü.]{2,15})", 
        text, 
        re.IGNORECASE
    )
    if nat_match:
        fields["nationality"] = nat_match.group(1).strip().upper()
    else:
        fields["nationality"] = "T.C. / TUR"
        
    # 9. Anne Adı / Baba Adı
    mother_match = re.search(r"(?:anne\s+adı?|mother'?s\s+name)\s*[:/]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü]+)", text, re.IGNORECASE)
    if mother_match:
        fields["mother_name"] = mother_match.group(1).strip().upper()
        
    father_match = re.search(r"(?:baba\s+adı?|father'?s\s+name)\s*[:/]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü]+)", text, re.IGNORECASE)
    if father_match:
        fields["father_name"] = father_match.group(1).strip().upper()
        
    return fields


def extract_invoice_fields(text: str) -> Dict[str, Any]:
    """Fatura dokümanından fatura no, tarih, toplam tutar ve KDV'yi ayıklar."""
    fields: Dict[str, Any] = {}
    
    inv_no = re.search(r"(?:fatura\s*no|invoice\s*no|fatura\s*numarası)\s*[:/]?\s*([A-Z0-9\-_]{6,20})", text, re.IGNORECASE)
    if inv_no:
        fields["invoice_no"] = inv_no.group(1).strip()
        
    date_match = re.search(r"(?:fatura\s*tarihi|invoice\s*date|tarih)\s*[:/]?\s*(\d{2}[./-]\d{2}[./-]\d{4})", text, re.IGNORECASE)
    if date_match:
        fields["invoice_date"] = date_match.group(1).strip()
        
    vkn_match = re.search(r"(?:vkn|vergi\s*kimlik\s*no|vergi\s*no)\s*[:/]?\s*(\d{10})\b", text, re.IGNORECASE)
    if vkn_match:
        fields["tax_id"] = vkn_match.group(1).strip()
        
    total_match = re.search(r"(?:genel\s*toplam|ödenecek\s*tutar|toplam\s*tutar|total\s*amount|total)\s*[:/]?\s*([\d.,]+\s*(?:TL|TRY|USD|EUR|₺|\$|€)?)", text, re.IGNORECASE)
    if total_match:
        fields["total_amount"] = total_match.group(1).strip()
        
    vat_match = re.search(r"(?:kdv\s*tutarı|kdv\s*toplamı|kdv\s*\(?%?\d*\)?|vat)\s*[:/]?\s*([\d.,]+\s*(?:TL|TRY|USD|EUR|₺|\$|€)?)", text, re.IGNORECASE)
    if vat_match:
        fields["vat_amount"] = vat_match.group(1).strip()
        
    return fields


def extract_bank_fields(text: str) -> Dict[str, Any]:
    """Banka dokümanı / dekontundan IBAN, bakiye ve hesap detaylarını ayıklar."""
    fields: Dict[str, Any] = {}
    
    iban_match = re.search(r"\b(TR\d{2}[\s\d]{20,26})\b", text)
    if iban_match and is_valid_iban(iban_match.group(1)):
        fields["iban"] = iban_match.group(1).replace(" ", "")
        
    balance_match = re.search(r"(?:kullanılabilir\s*bakiye|mevcut\s*bakiye|bakiye|balance)\s*[:/]?\s*([\d.,]+\s*(?:TL|TRY|USD|EUR|₺|\$|€)?)", text, re.IGNORECASE)
    if balance_match:
        fields["balance"] = balance_match.group(1).strip()
        
    return fields


def extract_contract_fields(text: str) -> Dict[str, Any]:
    """Sözleşme dokümanından taraf ve süre bilgilerini ayıklar."""
    fields: Dict[str, Any] = {}
    
    title_match = re.search(r"^([A-ZÇĞİÖŞÜ\s]{5,50}\s+SÖZLEŞMESİ)", text, re.MULTILINE)
    if title_match:
        fields["contract_title"] = title_match.group(1).strip()
        
    date_match = re.search(r"(?:yürürlük\s*tarihi|sözleşme\s*tarihi|imza\s*tarihi)\s*[:/]?\s*(\d{2}[./-]\d{2}[./-]\d{4})", text, re.IGNORECASE)
    if date_match:
        fields["effective_date"] = date_match.group(1).strip()
        
    return fields


def extract_structured_document_data(text: str, category: str) -> Dict[str, Any]:
    """
    Doküman kategorisine göre optimize edilmiş yapılandırılmış alan çıkarımı yapar.
    MRZ parsing, Cross-Validation ve Görsel PII tespitini birleştirir.
    """
    if not text:
        return {}
        
    result: Dict[str, Any] = {
        "document_type": category,
        "fields": {},
        "mrz_data": None,
        "cross_validation": None,
        "visual_pii": detect_visual_pii_elements(text, category=category)
    }
    
    # 1. MRZ Taraması (Kimlik veya Pasaport durumunda)
    mrz_parsed = parse_mrz(text)
    if mrz_parsed:
        result["mrz_data"] = mrz_parsed
        
    # 2. Kategori Bazlı Alan Çıkarımı
    if category in ("IDENTITY_CARD", "DRIVER_LICENSE", "PASSPORT"):
        extracted = extract_identity_card_fields(text)
        result["fields"] = extracted
        if mrz_parsed:
            result["cross_validation"] = cross_validate_mrz_with_text(mrz_parsed, extracted)
            # MRZ'den gelen doğrulanmış verileri text'te eksikse tamamla
            if not extracted.get("tckn") and mrz_parsed.get("tckn"):
                extracted["tckn"] = mrz_parsed["tckn"]
            if not extracted.get("document_no") and mrz_parsed.get("document_number"):
                extracted["document_no"] = mrz_parsed["document_number"]
            if not extracted.get("surname") and mrz_parsed.get("surname"):
                extracted["surname"] = mrz_parsed["surname"]
            if not extracted.get("given_name") and mrz_parsed.get("given_names"):
                extracted["given_name"] = mrz_parsed["given_names"]
            if not extracted.get("birth_date") and mrz_parsed.get("birth_date"):
                extracted["birth_date"] = mrz_parsed["birth_date"]
            if not extracted.get("valid_until") and mrz_parsed.get("expiry_date"):
                extracted["valid_until"] = mrz_parsed["expiry_date"]
    elif category == "INVOICE":
        result["fields"] = extract_invoice_fields(text)
    elif category == "BANK_DOCUMENT":
        result["fields"] = extract_bank_fields(text)
    elif category == "CONTRACT":
        result["fields"] = extract_contract_fields(text)
        
    return result

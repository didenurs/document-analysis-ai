import re
from typing import Optional, Dict, Any, List

# ICAO 9303 Mod 10 weighting factors: 7, 3, 1, 7, 3, 1...
MRZ_WEIGHTS = [7, 3, 1]

def calculate_mrz_check_digit(data: str) -> str:
    """
    ICAO Doc 9303 standardına göre Modulo 10 (Ağırlıklar: 7, 3, 1) kontrol basamağını hesaplar.
    """
    total = 0
    for idx, char in enumerate(data):
        weight = MRZ_WEIGHTS[idx % 3]
        if char == '<':
            val = 0
        elif char.isdigit():
            val = int(char)
        elif char.isalpha():
            # A=10, B=11 ... Z=35
            val = ord(char.upper()) - ord('A') + 10
        else:
            val = 0
        total += val * weight
    return str(total % 10)

def verify_mrz_checksum(data: str, expected_digit: str) -> bool:
    """Kontrol basamağının ICAO 9303'e göre doğruluğunu kontrol eder."""
    if not expected_digit or not expected_digit.isdigit():
        return False
    return calculate_mrz_check_digit(data) == expected_digit

def parse_date_yy_mm_dd(date_str: str) -> Optional[str]:
    """YYMMDD biçimini YYYY-MM-DD biçimine çevirir."""
    if not date_str or len(date_str) != 6 or not date_str.isdigit():
        return None
    yy = int(date_str[:2])
    mm = date_str[2:4]
    dd = date_str[4:6]
    # 00-40 -> 2000-2040; 41-99 -> 1941-1999
    century = "20" if yy <= 40 else "19"
    return f"{century}{yy:02d}-{mm}-{dd}"

def extract_mrz_lines_from_text(text: str) -> List[str]:
    """
    Metin içinden ICAO MRZ formatındaki satırları (TD1: 3 satır 30 krk, TD3: 2 satır 44 krk) ayıklar.
    Hem satır başı (\n) içeren metinleri hem de boşlukla birleştirilmiş metinleri destekler.
    """
    if not text:
        return []
        
    lines = [line.strip().replace(" ", "").upper() for line in text.splitlines() if line.strip()]
    candidate_lines = []
    
    for i, line in enumerate(lines):
        cleaned = re.sub(r'[^A-Z0-9<]', '', line)
        if cleaned.startswith(('I<', 'P<', 'V<', 'A<', 'C<')) or ('<' in cleaned and len(cleaned) >= 20):
            candidate_lines.append(cleaned)
        elif re.match(r'^\d{6,7}[MFX<]\d{6,7}[A-Z0-9<]{5,}', cleaned) and len(cleaned) >= 25:
            candidate_lines.append(cleaned)

    if len(candidate_lines) >= 2:
        return candidate_lines

    # Tek satırlık veya boşlukla ayrılmış metin fallback'i (TD1: 3 x 30 krk)
    upper_text = text.upper()
    td1_match = re.search(r'(I<[A-Z0-9<]{20,32})\s+([0-9]{6,7}[A-Z0-9<]{20,26})\s+([A-Z0-9<]{20,32})', upper_text)
    if td1_match:
        return [
            re.sub(r'[^A-Z0-9<]', '', td1_match.group(1)),
            re.sub(r'[^A-Z0-9<]', '', td1_match.group(2)),
            re.sub(r'[^A-Z0-9<]', '', td1_match.group(3))
        ]

    # TD3: 2 x 44 krk
    td3_match = re.search(r'(P<[A-Z0-9<]{30,46})\s+([A-Z0-9<]{30,46})', upper_text)
    if td3_match:
        return [
            re.sub(r'[^A-Z0-9<]', '', td3_match.group(1)),
            re.sub(r'[^A-Z0-9<]', '', td3_match.group(2))
        ]
            
    return candidate_lines


def parse_mrz_td1(lines: List[str]) -> Optional[Dict[str, Any]]:
    """
    TD1 Formatı (Ulusal Kimlik Kartı - 3 Satır x 30 Karakter)
    Satır 1: I<TUR[Belge No 9 krk][Knt 1 krk][Opsiyonel 15 krk]
    Satır 2: [Doğum YYMMDD][Knt 1][Cinsiyet 1][Geçerlilik YYMMDD][Knt 1][Uyruk 3][Opsiyonel/TCKN 11][Knt 1]
    Satır 3: [SOYAD]<<[AD]<[İKİNCİ_AD]<<<<<<<<
    """
    if len(lines) < 3:
        return None
        
    l1 = lines[0].ljust(30, '<')[:30]
    l2 = lines[1].ljust(30, '<')[:30]
    l3 = lines[2].ljust(30, '<')[:30]
    
    doc_type = l1[0:2].replace('<', '')
    issuer = l1[2:5].replace('<', '')
    doc_number = l1[5:14].replace('<', '')
    doc_num_check = l1[14:15]
    doc_num_valid = verify_mrz_checksum(l1[5:14], doc_num_check)
    
    dob_raw = l2[0:6]
    dob_check = l2[6:7]
    dob_valid = verify_mrz_checksum(dob_raw, dob_check)
    dob = parse_date_yy_mm_dd(dob_raw)
    
    sex = l2[7:8].replace('<', 'X')
    
    expiry_raw = l2[8:14]
    expiry_check = l2[14:15]
    expiry_valid = verify_mrz_checksum(expiry_raw, expiry_check)
    expiry = parse_date_yy_mm_dd(expiry_raw)
    
    nationality = l2[15:18].replace('<', '')
    
    # TCKN veya Opsiyonel alan (Genellikle Türk Kimliklerinde TCKN 11 hane satır 2 sonunda yer alır)
    opt_raw = l2[18:29].replace('<', '')
    tckn = opt_raw if len(opt_raw) == 11 and opt_raw.isdigit() else None
    
    # İsim ve Soyad (Satır 3)
    name_parts = l3.split('<<')
    surname = name_parts[0].replace('<', ' ').strip() if len(name_parts) > 0 else ""
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
    
    return {
        "format": "TD1",
        "document_type": "IDENTITY_CARD",
        "doc_type_code": doc_type,
        "issuing_country": issuer,
        "document_number": doc_number,
        "document_number_valid": doc_num_valid,
        "birth_date": dob,
        "birth_date_raw": dob_raw,
        "birth_date_valid": dob_valid,
        "sex": sex,
        "expiry_date": expiry,
        "expiry_date_raw": expiry_raw,
        "expiry_date_valid": expiry_valid,
        "nationality": nationality,
        "tckn": tckn,
        "surname": surname,
        "given_names": given_names,
        "full_name": f"{given_names} {surname}".strip(),
        "is_checksum_valid": doc_num_valid and dob_valid and expiry_valid,
        "raw_lines": [l1, l2, l3]
    }

def parse_mrz_td3(lines: List[str]) -> Optional[Dict[str, Any]]:
    """
    TD3 Formatı (Pasaport - 2 Satır x 44 Karakter)
    Satır 1: P<TUR[SOYAD]<<[AD]<[İKİNCİ_AD]<<<<<<<<<<<<<<<<<<<<
    Satır 2: [Pasaport No 9][Knt 1][Uyruk 3][Doğum YYMMDD][Knt 1][Cinsiyet 1][Geçerlilik YYMMDD][Knt 1][Opsiyonel/TCKN 14][Knt 1]
    """
    if len(lines) < 2:
        return None
        
    l1 = lines[0].ljust(44, '<')[:44]
    l2 = lines[1].ljust(44, '<')[:44]
    
    doc_type = l1[0:2].replace('<', '')
    issuer = l1[2:5].replace('<', '')
    
    # İsim ve Soyad (Satır 1: P<TUR'dan sonra)
    name_field = l1[5:]
    name_parts = name_field.split('<<')
    surname = name_parts[0].replace('<', ' ').strip() if len(name_parts) > 0 else ""
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
    
    # Satır 2
    doc_number = l2[0:9].replace('<', '')
    doc_num_check = l2[9:10]
    doc_num_valid = verify_mrz_checksum(l2[0:9], doc_num_check)
    
    nationality = l2[10:13].replace('<', '')
    
    dob_raw = l2[13:19]
    dob_check = l2[19:20]
    dob_valid = verify_mrz_checksum(dob_raw, dob_check)
    dob = parse_date_yy_mm_dd(dob_raw)
    
    sex = l2[20:21].replace('<', 'X')
    
    expiry_raw = l2[21:27]
    expiry_check = l2[27:28]
    expiry_valid = verify_mrz_checksum(expiry_raw, expiry_check)
    expiry = parse_date_yy_mm_dd(expiry_raw)
    
    # Opsiyonel alan (TCKN vb.)
    opt_raw = l2[28:42].replace('<', '')
    tckn = opt_raw[:11] if len(opt_raw) >= 11 and opt_raw[:11].isdigit() else None
    
    return {
        "format": "TD3",
        "document_type": "PASSPORT",
        "doc_type_code": doc_type,
        "issuing_country": issuer,
        "document_number": doc_number,
        "document_number_valid": doc_num_valid,
        "birth_date": dob,
        "birth_date_raw": dob_raw,
        "birth_date_valid": dob_valid,
        "sex": sex,
        "expiry_date": expiry,
        "expiry_date_raw": expiry_raw,
        "expiry_date_valid": expiry_valid,
        "nationality": nationality,
        "tckn": tckn,
        "surname": surname,
        "given_names": given_names,
        "full_name": f"{given_names} {surname}".strip(),
        "is_checksum_valid": doc_num_valid and dob_valid and expiry_valid,
        "raw_lines": [l1, l2]
    }

def parse_mrz(text: str) -> Optional[Dict[str, Any]]:
    """
    Metin içerisinden TD1 (3 satır) veya TD3 (2 satır) MRZ alanını otomatik tespit eder ve ayrıştırır.
    """
    if not text:
        return None
        
    mrz_candidates = extract_mrz_lines_from_text(text)
    if not mrz_candidates:
        return None
        
    # 1. Eğer 'I<' veya 'A<' veya 'C<' ile başlayan satır varsa TD1 (3 satır) önceliklidir
    has_td1_starter = any(l.startswith(('I<', 'A<', 'C<', 'I')) for l in mrz_candidates)
    has_td3_starter = any(l.startswith(('P<', 'P')) for l in mrz_candidates)
    
    if has_td1_starter and len(mrz_candidates) >= 3:
        parsed = parse_mrz_td1(mrz_candidates[:3])
        if parsed and (parsed["surname"] or parsed["document_number"]):
            return parsed
            
    if has_td3_starter and len(mrz_candidates) >= 2:
        parsed = parse_mrz_td3(mrz_candidates[:2])
        if parsed and (parsed["surname"] or parsed["document_number"]):
            return parsed
            
    # TD1: 3 satır dene
    if len(mrz_candidates) >= 3:
        parsed = parse_mrz_td1(mrz_candidates[:3])
        if parsed and (parsed["surname"] or parsed["document_number"]):
            return parsed
            
    # TD3: 2 satır dene
    if len(mrz_candidates) >= 2:
        parsed = parse_mrz_td3(mrz_candidates[:2])
        if parsed and (parsed["surname"] or parsed["document_number"]):
            return parsed
            
    return None

def cross_validate_mrz_with_text(mrz_data: Dict[str, Any], text_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    MRZ'den çıkarılan resmi alanlar ile OCR metin alanları arasındaki çapraz doğrulamayı (Cross-Validation) yapar.
    """
    if not mrz_data or not text_fields:
        return {"matches": {}, "all_matched": False, "confidence_boost": 0.0}
        
    matches = {}
    
    # 1. Belge Numarası Eşleşmesi
    if mrz_data.get("document_number") and text_fields.get("document_no"):
        mrz_doc = re.sub(r'\s+', '', str(mrz_data["document_number"])).upper()
        txt_doc = re.sub(r'\s+', '', str(text_fields["document_no"])).upper()
        matches["document_number"] = (mrz_doc == txt_doc or mrz_doc in txt_doc or txt_doc in mrz_doc)
        
    # 2. TCKN Eşleşmesi
    if mrz_data.get("tckn") and text_fields.get("tckn"):
        matches["tckn"] = (str(mrz_data["tckn"]) == str(text_fields["tckn"]))
        
    # 3. Soyad Eşleşmesi
    if mrz_data.get("surname") and text_fields.get("surname"):
        mrz_sur = mrz_data["surname"].upper()
        txt_sur = text_fields["surname"].upper()
        matches["surname"] = (mrz_sur == txt_sur or mrz_sur in txt_sur or txt_sur in mrz_sur)
        
    # 4. Doğum Tarihi Eşleşmesi
    if mrz_data.get("birth_date") and text_fields.get("birth_date"):
        matches["birth_date"] = True
        
    matched_count = sum(1 for v in matches.values() if v)
    total_checked = len(matches)
    
    return {
        "matches": matches,
        "matched_count": matched_count,
        "total_checked": total_checked,
        "all_matched": matched_count == total_checked if total_checked > 0 else False,
        "cross_validation_score": round(matched_count / total_checked, 2) if total_checked > 0 else 0.0
    }

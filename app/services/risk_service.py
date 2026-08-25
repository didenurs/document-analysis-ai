import re
from typing import Dict, Any

# ─────────────────────────────────────────────────────────────────
# ÜÇ BOYUTLU RİSK MODELİ (P0 fix)
# Önceki tek-skor sistemi yerine Security / Privacy / Sensitive Data
# ayrımı getiriliyor. IDENTITY_CARD → güvenlik riski düşük,
# gizlilik riski kritik. Bu ayrım UI'ya doğru yansır.
# ─────────────────────────────────────────────────────────────────

# ── Boyut 1: Güvenlik Tehdidi (Siber / Saldırı / Kötü Amaçlı) ──────
SECURITY_HIGH = [
    "data breach", "zero-day", "exploit", "ransomware", "malware",
    "data leak", "system compromise", "backdoor", "exfiltration", "hijack",
    "veri sızıntısı", "veri sizintisi", "sıfır gün", "fidye yazılımı",
    "zararlı yazılım", "kötü amaçlı yazılım", "arka kapı", "veri hırsızlığı",
    "sistem ele geçirme", "yetkisiz erişim",
]
SECURITY_MEDIUM = [
    "cyber attack", "vulnerability", "security threat", "phishing attack",
    "siber saldırı", "güvenlik zafiyeti", "güvenlik açığı", "siber tehdit",
    "oltalama saldırısı", "güvenlik ihlali",
]
SECURITY_LOW = [
    "security warning", "suspicious activity", "security patch", "audit finding",
    "güvenlik uyarısı", "şüpheli aktivite", "güvenlik yaması", "denetim bulgusu",
]
SECURITY_MITIGATORS = [
    "historical", "past incident", "simulation", "test scenario",
    "gecmis olay", "simulasyon", "test raporu", "giderildi", "cozuldu",
]
SECURITY_AMPLIFIERS = [
    "active attack", "currently compromised", "ongoing breach",
    "devam eden saldiri", "halihazırda", "kritik tehdit devam",
]

# ── Boyut 2: Gizlilik / PII (KVKK Kapsamındaki Kişisel Veri) ────────
PRIVACY_CRITICAL_TYPES = {
    "TCKN", "MRZ", "CREDIT_CARD", "IBAN", "API_KEY",
    "SERIAL_NO", "DOCUMENT_NUMBER",
}
PRIVACY_HIGH_TYPES = {
    "BIRTH_DATE", "PARENTS_NAME", "FULL_NAME", "EMAIL", "PHONE",
    "ADDRESS", "GENDER", "NATIONALITY", "EXPIRY_DATE",
}
PRIVACY_MEDIUM_TYPES = {
    "LICENSE_PLATE", "IP_ADDRESS", "NAME", "SOCIAL_PROFILE",
}

# Belge tipine göre otomatik gizlilik seviyesi
CATEGORY_PRIVACY_BASELINE: dict[str, str] = {
    "IDENTITY_CARD":    "CRITICAL",
    "PASSPORT":         "CRITICAL",
    "RESUME_CV":        "HIGH",
    "BANK_DOCUMENT":    "HIGH",
    "INVOICE":          "MEDIUM",
    "CONTRACT":         "MEDIUM",
    "MEDICAL_DOCUMENT": "CRITICAL",
    "LEGAL_DOCUMENT":   "HIGH",
    "ACADEMIC_DOCUMENT":"MEDIUM",
    "GENERAL_DOCUMENT": "LOW",
}

# ── Boyut 3: Hassas / Özel Nitelikli Veri ──────────────────────────
SENSITIVE_KEYWORDS = [
    "biyometrik", "biometric", "parmak izi", "fingerprint",
    "yüz tanıma", "face recognition", "retina", "retinal",
    "genetik veri", "genetic data", "dna", "sağlık verisi",
    "ırk", "etnik köken", "ethnic origin", "siyasi görüş",
    "dini inanç", "religious belief", "cinsel yönelim", "sexual orientation",
    "özel nitelikli", "ozel nitelikli", "sensitive category",
    "biyometrik imza", "biometric signature",
]

RISK_LEVEL_SCORES = {"LOW": 1, "MEDIUM": 3, "HIGH": 7, "CRITICAL": 10}

def _normalize(text: str) -> str:
    return (
        text
        .replace("İ", "i").replace("I", "ı")
        .replace("Ğ", "ğ").replace("Ş", "ş")
        .replace("Ü", "ü").replace("Ö", "ö")
        .replace("Ç", "ç")
        .lower()
    )

def _count_phrases(phrases: list[str], normalized_text: str) -> int:
    count = 0
    for phrase in phrases:
        pattern = rf"\b{re.escape(_normalize(phrase))}\b"
        count += len(re.findall(pattern, normalized_text))
    return count

def _level_from_score(score: int) -> str:
    if score == 0:
        return "LOW"
    elif score <= 4:
        return "MEDIUM"
    elif score <= 9:
        return "HIGH"
    return "CRITICAL"

def _score_from_level(level: str) -> int:
    return RISK_LEVEL_SCORES.get(level, 1)


def analyze_risk_multidimensional(
    text: str,
    category: str = "GENERAL_DOCUMENT",
    pii_entities: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Üç boyutlu risk analizi:
      - security_threat : Siber saldırı / kötü amaçlı yazılım riski
      - privacy_exposure : Kişisel veri / KVKK riski
      - sensitive_data   : Özel nitelikli / biyometrik veri riski
      - overall          : Üç boyutun maksimumu
    """
    if not text:
        return _empty_risk()

    normalized = _normalize(text)
    pii_entities = pii_entities or []

    # ── Boyut 1: Güvenlik Tehdidi ─────────────────────────────────
    high_cnt = _count_phrases(SECURITY_HIGH, normalized)
    med_cnt  = _count_phrases(SECURITY_MEDIUM, normalized)
    low_cnt  = _count_phrases(SECURITY_LOW, normalized)
    mitig_cnt = sum(1 for p in SECURITY_MITIGATORS if _normalize(p) in normalized)
    amp_cnt   = sum(1 for p in SECURITY_AMPLIFIERS if _normalize(p) in normalized)

    raw_sec = (high_cnt * 3) + (med_cnt * 2) + (low_cnt * 1)
    if mitig_cnt > 0 and amp_cnt == 0:
        sec_score = max(1, int(raw_sec * 0.5))
        incident_status = "Tarihi / Çözülmüş Rapor"
    elif amp_cnt > 0:
        sec_score = raw_sec + (amp_cnt * 3)
        incident_status = "🚨 Aktif Canlı Saldırı / Olay"
    elif raw_sec > 0:
        sec_score = raw_sec
        incident_status = "Potansiyel Güvenlik Riski"
    else:
        sec_score = 0
        incident_status = "Güvenlik Tehdidi Tespit Edilmedi"

    sec_level = _level_from_score(sec_score)

    # ── Boyut 2: Gizlilik / PII Riski ────────────────────────────
    pii_types = {e.get("type") for e in pii_entities}

    # Baseline — belge tipine göre minimum seviye
    baseline = CATEGORY_PRIVACY_BASELINE.get(category, "LOW")
    priv_score = _score_from_level(baseline)

    # PII varlıklarına göre yükselt
    critical_found = [t for t in PRIVACY_CRITICAL_TYPES if t in pii_types]
    high_found     = [t for t in PRIVACY_HIGH_TYPES     if t in pii_types]
    med_found      = [t for t in PRIVACY_MEDIUM_TYPES   if t in pii_types]

    priv_score += len(critical_found) * 3 + len(high_found) * 1 + len(med_found) * 0.5
    priv_score = int(min(priv_score, 10))
    priv_level = _level_from_score(priv_score)

    priv_factors = critical_found + high_found + med_found

    # ── Boyut 3: Hassas / Özel Nitelikli Veri ────────────────────
    sens_cnt = _count_phrases(SENSITIVE_KEYWORDS, normalized)
    # Biyometrik PII varlıkları
    if "BIOMETRIC_NOTICE" in pii_types:
        sens_cnt += 3
    sens_score = min(sens_cnt * 2, 10)
    sens_level = _level_from_score(sens_score)

    # ── Overall ───────────────────────────────────────────────────
    level_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    all_levels = [sec_level, priv_level, sens_level]
    overall_level = max(all_levels, key=lambda l: level_order.index(l))
    overall_score = max(sec_score, priv_score, sens_score)

    # Belge tipine özel incident_status
    if category == "IDENTITY_CARD":
        incident_status = "Kimlik Belgesi — Yüksek Gizlilik Riski"
    elif category == "RESUME_CV":
        incident_status = "Özgeçmiş — Kişisel Veri İçeriyor"
    elif category == "MEDICAL_DOCUMENT":
        incident_status = "Tıbbi Belge — Özel Nitelikli Veri"
    elif sec_score > 5:
        pass  # aktif saldırı mesajını koru

    return {
        "security_threat": {
            "score": sec_score,
            "level": sec_level,
            "factors": [],
        },
        "privacy_exposure": {
            "score": priv_score,
            "level": priv_level,
            "factors": priv_factors,
        },
        "sensitive_data": {
            "score": sens_score,
            "level": sens_level,
            "factors": ["Biyometrik/Özel Nitelikli"] if sens_score > 0 else [],
        },
        "overall": {
            "score": overall_score,
            "level": overall_level,
        },
        "incident_status": incident_status,
        "is_mitigated": mitig_cnt > 0 and amp_cnt == 0,
    }


def _empty_risk() -> dict[str, Any]:
    return {
        "security_threat": {"score": 0, "level": "LOW", "factors": []},
        "privacy_exposure": {"score": 0, "level": "LOW", "factors": []},
        "sensitive_data":   {"score": 0, "level": "LOW", "factors": []},
        "overall":          {"score": 0, "level": "LOW"},
        "incident_status":  "Risk Tespit Edilmedi",
        "is_mitigated":     False,
    }


# ── Geriye uyumluluk sarmalayıcısı ───────────────────────────────────
def analyze_risk(
    text: str,
    category: str = "GENERAL_DOCUMENT",
    pii_entities: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Geriye uyumlu sarmalayıcı. Eski kod `risk_score` ve `risk_level`
    anahtar sözcüklerine erişmeye devam edebilir.
    Yeni kod `risk_breakdown` üzerinden üç boyutlu veriyi kullanır.
    """
    result = analyze_risk_multidimensional(text, category, pii_entities)
    return {
        # Geriye uyumlu alanlar
        "risk_score":    result["overall"]["score"],
        "risk_level":    result["overall"]["level"],
        "incident_status": result["incident_status"],
        "is_mitigated":  result["is_mitigated"],
        # Yeni alan
        "risk_breakdown": result,
    }
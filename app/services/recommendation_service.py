from typing import List, Dict, Any
from app.models.schemas import ActionItem, KVKKReport, AnomalyReport

def generate_action_recommendations(
    category: str,
    risk_level: str,
    risk_score: int,
    kvkk_report: KVKKReport = None,
    anomaly_report: AnomalyReport = None
) -> List[ActionItem]:
    """
    Doküman analizi sonuçlarına göre güvenlik, uyum, hukuk ve operasyon ekipleri için
    önceliklendirilmiş aksiyon önerileri oluşturur.
    """
    items: List[ActionItem] = []

    # 1. Yüksek Risk Aksiyonları
    if risk_score >= 70 or risk_level == "High":
        items.append(ActionItem(
            priority="High",
            category="Security",
            title="🚨 Acil Güvenlik İzolasyonu ve Olay Müdahalesi",
            description="Tespit edilen yüksek güvenlik riski nedeniyle etkilenen sunucu/sistemleri derhal izole edin ve kimlik bilgilerini sıfırlayın."
        ))
        items.append(ActionItem(
            priority="High",
            category="Operational",
            title="🔍 Adli Bilişim & Log İncelemesi",
            description="Son 48 saate ait erişim loglarını ve güvenlik duvarı kayıtlarını adli bilişim ekibine ileterek sızıntı alanını belirleyin."
        ))
    elif risk_score >= 35 or risk_level == "Medium":
        items.append(ActionItem(
            priority="Medium",
            category="Security",
            title="⚠️ Güvenlik Yaması ve Erişim Gözden Geçirme",
            description="Dokümanda belirtilen potansiyel güvenlik açıklarını kapatın ve yetkisiz erişim haklarını kısıtlayın."
        ))

    # 2. KVKK / GDPR Uyum Aksiyonları
    if kvkk_report and kvkk_report.total_entities > 0:
        p_priority = "High" if kvkk_report.total_entities > 5 else "Medium"
        items.append(ActionItem(
            priority=p_priority,
            category="Compliance",
            title="🛡️ Hassas Veri (PII) Şifreleme ve Erişim Kısıtlaması",
            description=f"Dokümanda tespit edilen {kvkk_report.total_entities} adet kişisel/hassas veriyi (TCKN/IBAN/Tel) maskeleyin ve veritabanında şifrelenmiş olarak saklayın."
        ))
        items.append(ActionItem(
            priority="Medium",
            category="Compliance",
            title="📜 KVKK Veri Sorumlusu İrtibat Bildirimi",
            description="Kişisel veri içeren bu dokümanın işlenme amacını ve saklama süresini VERBİS / Uyum envanterine kaydedin."
        ))

    # 3. Anomali & Manipülasyon Aksiyonları
    if anomaly_report and anomaly_report.has_anomaly:
        items.append(ActionItem(
            priority="High",
            category="Legal",
            title="⚖️ Belge Doğrulama ve İmza Denetimi",
            description="Dokümanda tespit edilen anomali göstergeleri nedeniyle resmi imza, tarih ve fatura tutarlarını onay mekanizmasından geçirin."
        ))

    # 4. Genel Kategorik Aksiyonlar
    if category.lower() in ["finance", "finans"]:
        items.append(ActionItem(
            priority="Low",
            category="Operational",
            title="📊 Muhasebe Mutabakatı",
            description="Raporlanan finansal tutarları ve kâr marjlarını ana muhasebe defteri ile eşleştirin."
        ))
    elif category.lower() in ["legal", "hukuk"]:
        items.append(ActionItem(
            priority="Low",
            category="Legal",
            title="📑 Hukuki Sorumluluk Maddeleri İncelemesi",
            description="Sözleşmedeki ceza koşullarını ve yetkili mahkeme maddelerini hukuk danışmanına iletin."
        ))

    # Varsayılan Aksiyon (Hiçbir risk/veri yoksa)
    if not items:
        items.append(ActionItem(
            priority="Low",
            category="Operational",
            title="✅ Rutin Doküman Arşivleme",
            description="Belge güvenli olarak değerlendirilmiştir; standart arşivleme protokolünü uygulayabilirsiniz."
        ))

    return items

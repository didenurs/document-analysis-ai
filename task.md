# Görev İlerleme Takibi

## ✅ Bölüm 1 — P0 (Tamamlandı & Canlıda)
- [x] 1. `category_service.py` — Deterministic taxonomy (IDENTITY_CARD, RESUME_CV, PASSPORT, ...)
- [x] 2. `risk_service.py` — Üç boyutlu risk: security_threat / privacy_exposure / sensitive_data
- [x] 3. `ner_service.py` — KVKK dili düzeltmesi + yeni PII entities (DocumentNumber, ExpiryDate, Gender, SocialProfile, ParentsName)
- [x] 4. `schemas.py` — risk_breakdown + redaction_verification alanları
- [x] 5. `routes.py` — İkinci PII taraması (residual scan) + yeni entity/risk mapping
- [x] 6. `cv_service.py` + `summary_service.py` — CV hallucination düzeltmesi
- [x] 7. `app.js` — Residual-bazlı "Temiz" mesajı + üçlü risk UI + buildRiskBreakdownHtml
- [x] 8. Testleri çalıştır → 74/74 PASS doğrulandı
- [x] 9. Git commit + deploy (canlıya alındı - a655a91)

## ✅ Bölüm 2 — P1 (Tamamlandı & Canlıda)
- [x] 1. `mrz_service.py` — ICAO Doc 9303 MRZ Parser (TD1 3-satır Kimlik, TD3 2-satır Pasaport), Mod 10 Checksum doğrulama ve Çapraz Doğrulama
- [x] 2. `document_extractor.py` — Yapılandırılmış Resmi Alan Çıkarımı (TCKN, Soyad, Ad, Doğum Tarihi, Belge No, Geçerlilik, Fatura, Banka)
- [x] 3. `document_extractor.py` — Görsel ve Biyometrik PII Tespiti (📸 Fotoğraf, ✍️ İmza, 🪪 Çip/Hologram, 🏁 Barkod/QR)
- [x] 4. `ocr_service.py` — Görsel Ön İşleme Hattı (Upscaling, Grayscale, Contrast/Sharpness optimizasyonu) ve OCR meta verileri
- [x] 5. `keyword_service.py` — Doküman Türüne Duyarlı Anahtar Kelime Çıkarımı (Kimlik/CV/Sözleşme şablon kelimelerini filtreleme)
- [x] 6. `schemas.py` & `routes.py` — `structured_data`, `mrz_data`, `visual_pii`, `ocr_metadata` alanlarının pipeline'a entegrasyonu
- [x] 7. `frontend/app.js` — Yapılandırılmış Doküman Kartı, MRZ Doğrulama Rozeti ve Görsel PII etiketleri arayüze eklendi
- [x] 8. Testleri çalıştır → 81/81 PASS doğrulandı
- [x] 9. Git commit + deploy (canlıya alındı - 779d631)

## 🚀 Bölüm 3 — P2 (Mimari Birleştirme & Export İyileştirmeleri)
- [x] 1. `export_service.py` — HTML Raporu için Benzersiz Report ID (`DOC-YYYYMMDD-...`), Engine Version (`v2.5-intelligence`), Doğrulama Rozeti (`✅ REDACTION VERIFIED`), 3 Boyutlu Risk Kartları, Yapılandırılmış Alanlar ve MRZ blokları
- [x] 2. `frontend/app.js` — Maskeli metin kutusu içine tek tıkla `📥 Maskelenmiş PDF İndir` butonu entegrasyonu
- [x] 3. `tests/test_audit_enhancements.py` — HTML Report ID, Doğrulama Rozetleri ve Export uç noktaları testleri
- [/] 4. 83+ Test ile tam doğrulama (Çalışıyor)
- [ ] 5. Git commit + deploy ile canlıya alma

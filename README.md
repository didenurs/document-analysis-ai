# AI-Powered Document Analysis and Risk Assessment System

Bu proje, yüklenen **PDF** belgelerini ve **düz metinleri** gelişmiş Doğal Dil İşleme (NLP) ve Transformer modelleri kullanarak analiz eden, özetleyen, kategorize eden, anahtar kelimelerini çıkaran ve güvenlik risk skorunu hesaplayan bir **FastAPI** backend ve **Modern Web Arayüzü** projesidir.

---

## 🚀 Özellikler

* **📄 PDF & Metin İşleme:** Düz metin ve PDF dosyalarından (`PyMuPDF`) metin çıkarma ve ön işleme.
* **📝 Akıllı Özetleme (Smart Summarization):** Hugging Face `sshleifer/distilbart-cnn-12-6` modeli ve uzun metinler için parçalama (chunking) algoritması ile kayıpsız özetleme.
* **🔑 Anahtar Kelime Çıkarımı:** `KeyBERT` (Sentence-Transformers) ile semantik anahtar kelimeler ve n-gram'lar çıkarma.
* **📁 Sıfır Örnekli Sınıflandırma (Zero-Shot Classification):** `valhalla/distilbart-mnli-12-1` modeli ile metinleri önceden tanımlanmış kategorilere (*Technology, Finance, Healthcare, Cyber Security, Education*) ayırma.
* **🛡️ Güvenlik ve Risk Değerlendirmesi:** Regex kelime sınırları (`\b`) ve ağırlıklı tehdit göstergeleriyle risk seviyesi (*Low, Medium, High*) ve puanı hesaplama.
* **💻 Modern Kullanıcı Arayüzü:** TailwindCSS, dark mode neon teması ve sürükle-bırak PDF yükleme desteği olan tek sayfalık web arayüzü.
* **🧪 Kapsamlı Test Takımı:** `pytest` ile tüm servisleri ve API endpoint'lerini kapsayan birim ve entegrasyon testleri.

---

## 🛠️ Teknoloji Yığını

* **Programlama Dili:** Python 3.12+
* **Backend:** FastAPI, Uvicorn, Pydantic
* **Yapay Zeka & NLP:** HuggingFace Transformers, PyTorch, KeyBERT, Sentence-Transformers
* **Doküman İşleme:** PyMuPDF (`fitz`)
* **Test:** Pytest, HTTPX
* **Frontend:** HTML5, TailwindCSS, Vanilla JS, CSS3 Animations

---

## 📁 Proje Mimarisi

```text
document-analysis-ai/
├── app/
│   ├── api/
│   │   └── routes.py           # FastAPI rotaları (/health, /analyze-text, /analyze-pdf)
│   ├── models/
│   │   └── schemas.py          # Pydantic veri modelleri (Request & Response)
│   ├── services/
│   │   ├── category_service.py # Zero-Shot sınıflandırma servisi
│   │   ├── keyword_service.py  # KeyBERT anahtar kelime servisi
│   │   ├── pdf_service.py      # PDF metin ayrıştırma servisi
│   │   ├── risk_service.py     # Risk değerlendirme ve puanlama motoru
│   │   └── summary_service.py  # Akıllı chunking destekli özetleme servisi
│   ├── utils/
│   │   └── text_cleaner.py     # Metin temizleme yardımcı fonksiyonları
│   └── main.py                 # FastAPI ana uygulama ve CORS yapılandırması
├── frontend/
│   ├── index.html              # Modern Web Arayüzü
│   ├── style.css               # Neon teması ve özel animasyonlar
│   └── app.js                  # Frontend API bağlantısı ve etkileşim mantığı
├── tests/
│   ├── test_api.py             # API entegrasyon testleri
│   ├── test_services.py        # NLP ve servis birim testleri
│   ├── analyze-pdf.pdf         # Test PDF dosyası
│   └── analyze-text.txt        # Test metin dosyası
├── pytest.ini                  # Pytest yapılandırması
├── requirements.txt            # Python bağımlılıkları (UTF-8)
└── README.md
```

---

## 💻 Kurulum ve Çalıştırma

### 1. Sanal Ortamı Hazırlama ve Bağımlılıkları Yükleme
```bash
# Sanal ortam oluşturma
python -m venv venv

# Sanal ortamı aktif etme (Windows)
.\venv\Scripts\activate

# Bağımlılıkları yükleme
pip install -r requirements.txt
```

### 2. Backend API'yi Başlatma
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
* **Swagger API Dokümantasyonu:** `http://127.0.0.1:8000/docs`
* **Health Check:** `http://127.0.0.1:8000/health`

### 3. Web Arayüzünü Açma
`frontend/index.html` dosyasını tarayıcınızda açabilir veya yerel bir canlı sunucu (`Live Server` / `python -m http.server`) ile görüntüleyebilirsiniz.

### 4. Testleri Çalıştırma
```bash
pytest -v
```
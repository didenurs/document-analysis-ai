# AI-Powered Document Analysis and Risk Assessment System

Bu proje, yüklenen **PDF** belgelerini ve **düz metinleri** gelişmiş Doğal Dil İşleme (NLP) ve Transformer modelleri kullanarak analiz eden, özetleyen, kategorize eden, anahtar kelimelerini çıkaran ve güvenlik risk skorunu hesaplayan bir **FastAPI** backend ve **Modern Web Arayüzü** projesidir.

---

## 🚀 Özellikler

* **📄 PDF & Metin İşleme:** Düz metin ve PDF dosyalarından (`PyMuPDF`) metin çıkarma ve ön işleme.
* **🌐 Çok Dilli Destek & Dil Tespiti:** Türkçe (`tr`) ve İngilizce (`en`) dokümanları otomatik algılama ve analiz etme.
* **📝 Akıllı ve Öz Çıkarımlı Özetleme:** Kısa metinlerde yan tümce ve ana fikir damıtma, uzun metinlerde bilgi yoğunluklu ve pozisyonel ağırlıklı özetleme.
* **🔑 Anahtar Kelime Çıkarımı:** `KeyBERT` ve çok dilli durak kelime filtreleme ile semantik anahtar kelimeler çıkarma.
* **📁 Çok Dilli Kategori Sınıflandırma:** Türkçe ve İngilizce sözlük eşleşmesiyle metinleri (*Technology, Finance, Healthcare, Cyber Security, Education, Legal*) kategorilerine ayırma.
* **🛡️ Güvenlik ve Risk Değerlendirmesi:** Türkçe ve İngilizce tehdit göstergeleriyle risk seviyesi (*Low, Medium, High*) ve puanı hesaplama.
* **💻 Modern Kullanıcı Arayüzü:** TailwindCSS, dark mode neon teması, tek tıkla Türkçe/İngilizce örnek yükleme ve sürükle-bırak PDF desteği.
* **🧪 Kapsamlı Test Takımı:** `pytest` ile tüm servisleri, dil tespitini ve API endpoint'lerini kapsayan 24 adet birim ve entegrasyon testi.

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
│   │   ├── category_service.py # Çok dilli kategori sınıflandırma servisi
│   │   ├── keyword_service.py  # Dil duyarlı anahtar kelime servisi
│   │   ├── llm_service.py      # Groq LPU (LLaMA 3.3) ultra hızlı soyutlayıcı özetleme
│   │   ├── pdf_service.py      # PDF metin ayrıştırma servisi
│   │   ├── risk_service.py     # Çok dilli risk değerlendirme ve puanlama motoru
│   │   └── summary_service.py  # Hibrit (LLM + Akıllı Fallback) özetleme servisi
│   ├── utils/
│   │   ├── language_detector.py # Otomatik dil tespit modülü
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
├── .env.example                # Ortam değişkenleri şablonu (Groq API)
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

### 2. Groq LLM API Yapılandırması (İsteğe Bağlı - Ücretsiz)
Metinlerin cımbızla seçilmek yerine insan gibi baştan, akıcı ve özgün yazılması için:
1. [Groq Console](https://console.groq.com/keys) adresinden ücretsiz bir API anahtarı alın.
2. `.env` dosyasına anahtarınızı ekleyin:
```env
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LLM_ENABLED=true
```
*(Not: API anahtarı girilmediğinde sistem otomatik olarak yerel akıllı sentezleyiciye geçer.)*

### 3. Backend API'yi Başlatma
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
* **Swagger API Dokümantasyonu:** `http://127.0.0.1:8000/docs`
* **Health Check:** `http://127.0.0.1:8000/health`

### 4. Web Arayüzünü Açma
`frontend/index.html` dosyasını tarayıcınızda açabilir veya yerel bir canlı sunucu (`Live Server` / `python -m http.server`) ile görüntüleyebilirsiniz.

### 5. Testleri Çalıştırma
```bash
pytest -v
```
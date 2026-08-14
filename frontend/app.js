const tabPdf = document.getElementById('tab-pdf');
const tabText = document.getElementById('tab-text');
const pdfSection = document.getElementById('pdf-section');
const textSection = document.getElementById('text-section');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const textInput = document.getElementById('text-input');
const analyzeTextBtn = document.getElementById('analyze-text-btn');
const clearTextBtn = document.getElementById('clear-text-btn');
const charCount = document.getElementById('char-count');
const toastContainer = document.getElementById('toast-container');

const loader = document.getElementById('loader');
const loaderTitle = document.getElementById('loader-title');
const loaderSubtext = document.getElementById('loader-subtext');
const resultsDiv = document.getElementById('results');

// Desteklenen Görsel Formatları
const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp'];

// Otomatik API URL Tespiti (Lokal geliştirme veya canlı Render ortamı)
function getApiBaseUrl() {
    if (window.location.protocol === 'file:') {
        return 'http://127.0.0.1:8000';
    }
    return '';
}

const API_URL = getApiBaseUrl();
console.log(`[API Bağlantısı] Hedef Adres: ${API_URL}`);

let activeTab = 'pdf';

// Aktif Analiz ve Çeviri Durumu
let activeAnalysisData = null;
let currentSummaryOriginal = "";
let currentSummaryTranslated = null;
let isShowingTranslation = false;

// Sekme Değiştirme
tabPdf.addEventListener('click', () => {
    activeTab = 'pdf';
    tabPdf.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-blue-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-2';
    tabText.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    
    pdfSection.classList.remove('hidden');
    textSection.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    hideToast();
});

tabText.addEventListener('click', () => {
    activeTab = 'text';
    tabText.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-blue-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-2';
    tabPdf.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    
    textSection.classList.remove('hidden');
    pdfSection.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    hideToast();
});

// Karakter Sayacı
textInput.addEventListener('input', () => {
    const len = textInput.value.length;
    charCount.textContent = `${len} karakter`;
});

// Temizle Butonu
clearTextBtn.addEventListener('click', () => {
    textInput.value = '';
    charCount.textContent = '0 karakter';
    hideToast();
});

// Çok Dilli Hızlı Örnekler
const SAMPLES = {
    // Türkçe Örnekler
    tr_cyber: "GİZLİ OLAY RAPORU: ACİL SALDIRI MÜDAHALESİ GEREKLİDİR Saat 02:00 sularında dahili izleme sistemlerimiz, merkezi kurumsal ağımızın birincil veritabanı güvenlik duvarında kritik bir arıza tespit etti. Son derece koordineli bir siber saldırı, bulut altyapımızda yeni keşfedilen bir sıfır gün güvenlik açığını başarıyla istismar ederek benzeri görülmemiş büyüklükte bir veri ihlaline yol açtı. Kötü niyetli saldırganlar ikincil kimlik doğrulama protokollerini ve şifreleme katmanlarını atlatmayı başararak müşterilerimizin son derece gizli finansal kayıtları için ciddi bir tehdit oluşturdu. Güvenliği ihlal edilen sunucular derhal izole edilip çevrimdışı bırakılmazsa büyük bir veri sızıntısının gerçekleşme olasılığı yüksek olduğundan, küresel olay müdahale ekibimiz tüm departmanlarda resmi olarak acil durum ilan etti. Tüm sistem yöneticilerinin, geliştiricilerin ve personelin kimlik bilgilerini sıfırlaması ve tespit edilen güvenlik açığını bir saat içinde yamaması kesinlikle ve acilen gerekmektedir. Bu ihlal, operasyonel bütünlüğümüz ve pazar itibarımız için kritik bir tehdit oluşturmaktadır. Saldırının tam kapsamını anlamak ve gelecekte başka bir saldırıyı veya yıkıcı sistem çökmesini önlemek amacıyla acil bir güvenlik denetimi ve adli bilişim analizi yürütülmektedir.",
    tr_finance: "Üçüncü Çeyrek Finansal Raporu: Şirketimiz bulut ve yapay zekâ yazılım ürünlerine olan yüksek talep sayesinde faaliyet gelirlerinde %28 oranında rekor büyüme kaydetti. İşletme giderleri %6 oranında azalırken net kâr marjı güçlendi ve serbest nakit akışı genişledi.",
    tr_short: "Bugün üniversitede yapay zekâ ve derin öğrenme modelleri üzerine kapsamlı bir ders işlendi.",
    
    // İngilizce Örnekler
    en_cyber: "CONFIDENTIAL INCIDENT REPORT: IMMEDIATE ATTACK RESPONSE REQUIRED At 02:00 AM standard time, our internal monitoring systems detected a critical failure in the primary database firewall of our central corporate network. A highly coordinated cyber attack successfully exploited a newly discovered zero-day vulnerability in our cloud infrastructure, leading to a massive and unprecedented data breach. The malicious actors managed to bypass the secondary authentication protocols and encryption layers, posing a severe threat to our clients' highly confidential financial records. Our global incident response team has officially declared a state of emergency across all departments, as there is a high probability of an imminent data leak if the compromised servers are not isolated and taken offline immediately. It is absolutely urgent that all system administrators, developers, and staff reset their credentials and patch the identified vulnerability within the next hour. This breach represents a critical threat to our operational integrity and overall market reputation. An urgent security audit and forensic analysis are currently underway to understand the full scope of the intrusion and to prevent any further attack or catastrophic system failure in the near future.",
    en_finance: "Quarterly Financial Overview: The company achieved a record 24% growth in operating revenue driven by strong enterprise software adoption. Operating expenses decreased by 8%, resulting in improved net profit margins and sustainable free cash flow expansion.",
    en_short: "FastAPI is a modern, high-performance web framework for building APIs with Python.",
    
    // Eski düğmelerle geriye dönük uyumluluk
    cyber: "CONFIDENTIAL INCIDENT REPORT: IMMEDIATE ATTACK RESPONSE REQUIRED At 02:00 AM standard time, our internal monitoring systems detected a critical failure in the primary database firewall of our central corporate network.",
    finance: "Quarterly Financial Overview: The company achieved a record 24% growth in operating revenue driven by strong enterprise software adoption.",
    short: "I went to school today."
};

function loadSample(type) {
    if (SAMPLES[type]) {
        textInput.value = SAMPLES[type];
        charCount.textContent = `${textInput.value.length} karakter`;
        if (activeTab !== 'text') {
            tabText.click();
        }
        hideToast();
    }
}
window.loadSample = loadSample;

// Dosya Seçme / Drag-Drop
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-500', 'bg-slate-800/50');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-500', 'bg-slate-800/50');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-500', 'bg-slate-800/50');
    if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
});

// Güvenli Response Ayrıştırma Yardımcısı
async function parseApiResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    
    if (contentType.includes("application/json")) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Sunucu işlem sırasında bir hata bildirdi.");
        }
        return data;
    }
    
    const rawText = await response.text();
    if (response.status === 502 || response.status === 503 || response.status === 504) {
        throw new Error("Sunucu şu anda uyanıyor (Render Cold Start). Lütfen 15-20 saniye sonra tekrar deneyin.");
    }
    if (!response.ok) {
        throw new Error(`Sunucu Hatası (${response.status}). Lütfen tekrar deneyin.`);
    }
    throw new Error("Beklenmeyen yanıt biçimi alındı.");
}

// Dosya (PDF veya Görsel) İşleme & Gönderme
async function handleFile(file) {
    const fileName = file.name.toLowerCase();
    const isPdf = fileName.endsWith('.pdf');
    const isImage = IMAGE_EXTENSIONS.some(ext => fileName.endsWith(ext));

    if (!isPdf && !isImage) {
        showToast("Lütfen sadece geçerli bir .PDF veya Görsel (.PNG, .JPG, .JPEG, .WEBP) dosyası seçin.", "warning");
        return;
    }

    if (file.size > 15 * 1024 * 1024) {
        showToast("Dosya boyutu çok büyük (Maksimum 15 MB).", "warning");
        return;
    }

    setLoading(true);
    if (isImage) {
        if (loaderTitle) loaderTitle.textContent = "Görsel OCR ile Taranıyor";
        if (loaderSubtext) loaderSubtext.textContent = "AI Vision & OCR motoru ile görseldeki metinler okunuyor ve analiz ediliyor...";
    } else {
        if (loaderTitle) loaderTitle.textContent = "Yapay Zekâ Analiz Ediyor";
        if (loaderSubtext) loaderSubtext.textContent = "PDF ayrıştırılıyor, taranmış sayfalar OCR ile taranıyor ve özetleniyor...";
    }
    hideToast();

    const formData = new FormData();
    formData.append("file", file);

    const endpoint = isPdf ? `${API_URL}/analyze-pdf` : `${API_URL}/analyze-image`;

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            body: formData
        });

        const data = await parseApiResponse(response);
        displayResults(data);
    } catch (error) {
        showToast(error.message, "error");
        setLoading(false);
    }
}

// Metin Gönderme
analyzeTextBtn.addEventListener('click', async () => {
    const textContent = textInput.value.trim();
    if (!textContent) {
        showToast("Lütfen analiz edilecek bir metin girin.", "warning");
        return;
    }

    setLoading(true);
    if (loaderTitle) loaderTitle.textContent = "Metin Analiz Ediliyor";
    if (loaderSubtext) loaderSubtext.textContent = "Groq LLaMA-3.3 ile soyutlayıcı özetleme, sınıflandırma ve risk analizi yapılıyor...";
    hideToast();

    try {
        const response = await fetch(`${API_URL}/analyze-text`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: textContent })
        });

        const data = await parseApiResponse(response);
        displayResults(data);
    } catch (error) {
        showToast(error.message, "error");
        setLoading(false);
    }
});

// Toast / Bildirim
function showToast(message, type = "info") {
    toastContainer.className = "mb-4 p-3.5 rounded-xl text-xs sm:text-sm flex items-start gap-2.5 transition-all animate-fade-in";
    
    let icon = "ℹ️";
    if (type === "error") {
        toastContainer.className += " bg-rose-500/10 border border-rose-500/30 text-rose-300";
        icon = "⚠️";
    } else if (type === "warning") {
        toastContainer.className += " bg-amber-500/10 border border-amber-500/30 text-amber-300";
        icon = "⚡";
    } else {
        toastContainer.className += " bg-blue-500/10 border border-blue-500/30 text-blue-300";
    }
    
    toastContainer.innerHTML = `
        <span class="text-base leading-none">${icon}</span>
        <div class="flex-1 font-medium">${message}</div>
        <button onclick="hideToast()" class="opacity-60 hover:opacity-100 ml-1 text-sm font-bold">&times;</button>
    `;
    toastContainer.classList.remove('hidden');
}

function hideToast() {
    toastContainer.classList.add('hidden');
}
window.hideToast = hideToast;

// Yükleme Durumu
function setLoading(isLoading) {
    if (isLoading) {
        pdfSection.classList.add('hidden');
        textSection.classList.add('hidden');
        tabPdf.parentElement.classList.add('hidden');
        resultsDiv.classList.add('hidden');
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
        tabPdf.parentElement.classList.remove('hidden');
        if (activeTab === 'pdf') {
            pdfSection.classList.remove('hidden');
        } else {
            textSection.classList.remove('hidden');
        }
    }
}

// Reset
function resetAnalysis() {
    resultsDiv.classList.add('hidden');
    resultsDiv.innerHTML = '';
    textInput.value = '';
    charCount.textContent = '0 karakter';
    fileInput.value = '';
    activeAnalysisData = null;
    currentSummaryOriginal = "";
    currentSummaryTranslated = null;
    isShowingTranslation = false;
    hideToast();
    setLoading(false);
}
window.resetAnalysis = resetAnalysis;

// Özeti Panoya Kopyalama
function copySummary() {
    const summaryText = document.getElementById('summary-content')?.innerText || '';
    if (summaryText) {
        navigator.clipboard.writeText(summaryText).then(() => {
            const btn = document.getElementById('copy-btn');
            if (btn) {
                const oldHtml = btn.innerHTML;
                btn.innerHTML = '✓ Kopyalandı';
                btn.classList.add('text-emerald-400', 'border-emerald-500/50');
                setTimeout(() => {
                    btn.innerHTML = oldHtml;
                    btn.classList.remove('text-emerald-400', 'border-emerald-500/50');
                }, 2000);
            }
        });
    }
}
window.copySummary = copySummary;

// Özet Çevirisi (TR <-> EN Çift Yönlü Çeviri)
async function toggleSummaryTranslation() {
    const summaryEl = document.getElementById('summary-content');
    const translateBtn = document.getElementById('translate-btn');
    const langBadge = document.getElementById('summary-lang-indicator');
    if (!summaryEl || !translateBtn || !activeAnalysisData) return;

    const originalLang = activeAnalysisData.language || 'en';
    const targetLang = (originalLang === 'tr') ? 'en' : 'tr';
    const targetLabel = (targetLang === 'tr') ? 'Türkçe' : 'English';
    const originalLabel = (originalLang === 'tr') ? 'Türkçe' : 'English';

    // 1. Durum: Zaten çeviri gösteriliyorsa orijinale geri dön
    if (isShowingTranslation) {
        summaryEl.textContent = currentSummaryOriginal;
        isShowingTranslation = false;
        translateBtn.innerHTML = `🌐 ${targetLabel}'ye Çevir`;
        translateBtn.classList.remove('bg-indigo-600/30', 'border-indigo-500/60', 'text-indigo-300');
        translateBtn.classList.add('bg-slate-900', 'border-slate-700', 'text-slate-300');
        if (langBadge) {
            langBadge.textContent = originalLabel;
            langBadge.className = originalLang === 'tr' ? 'lang-badge-tr' : 'lang-badge-en';
        }
        return;
    }

    // 2. Durum: Daha önce çevrildiyse önbellekten (cache) anında getir
    if (currentSummaryTranslated) {
        summaryEl.textContent = currentSummaryTranslated;
        isShowingTranslation = true;
        translateBtn.innerHTML = `🔄 Orijinale Dön (${originalLabel})`;
        translateBtn.classList.add('bg-indigo-600/30', 'border-indigo-500/60', 'text-indigo-300');
        if (langBadge) {
            langBadge.textContent = `${targetLabel} (Çeviri)`;
            langBadge.className = targetLang === 'tr' ? 'lang-badge-tr' : 'lang-badge-en';
        }
        return;
    }

    // 3. Durum: İlk kez çeviri yapılıyor -> API'ye sor
    const oldBtnContent = translateBtn.innerHTML;
    translateBtn.innerHTML = `⏳ Çevriliyor...`;
    translateBtn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/translate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: currentSummaryOriginal,
                target_language: targetLang
            })
        });

        const data = await parseApiResponse(response);
        currentSummaryTranslated = data.translated_text;
        summaryEl.textContent = currentSummaryTranslated;
        isShowingTranslation = true;
        translateBtn.innerHTML = `🔄 Orijinale Dön (${originalLabel})`;
        translateBtn.classList.add('bg-indigo-600/30', 'border-indigo-500/60', 'text-indigo-300');
        if (langBadge) {
            langBadge.textContent = `${targetLabel} (Çeviri)`;
            langBadge.className = targetLang === 'tr' ? 'lang-badge-tr' : 'lang-badge-en';
        }
    } catch (err) {
        showToast(`Çeviri işlemi başarısız oldu: ${err.message}`, "warning");
        translateBtn.innerHTML = oldBtnContent;
    } finally {
        translateBtn.disabled = false;
    }
}
window.toggleSummaryTranslation = toggleSummaryTranslation;

// Risk Rozeti
function getRiskBadge(level, score) {
    if (level === 'High') {
        return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/15 border border-rose-500/40 text-rose-400 font-extrabold text-xs">🚨 Yüksek Risk (Skor: ${score})</span>`;
    } else if (level === 'Medium') {
        return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-400 font-extrabold text-xs">⚠️ Orta Risk (Skor: ${score})</span>`;
    }
    return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 font-extrabold text-xs">🛡️ Düşük Risk (Skor: ${score})</span>`;
}

// Okuma Yöntemi Rozeti
function getMethodBadge(method, pageCount) {
    let methodText = '✍️ Metin Girişi';
    let badgeClass = 'bg-slate-800 text-slate-300 border-slate-700';

    if (method === 'vision_ocr') {
        methodText = '⚡ AI Vision OCR';
        badgeClass = 'bg-purple-500/15 text-purple-300 border-purple-500/40';
    } else if (method === 'tesseract_ocr' || method === 'ocr') {
        methodText = '🔍 OCR (Taranmış Doküman)';
        badgeClass = 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40';
    } else if (method === 'digital') {
        methodText = '📄 Dijital PDF Metni';
        badgeClass = 'bg-blue-500/15 text-blue-300 border-blue-500/40';
    }

    const pages = pageCount ? `<span class="ml-1.5 opacity-80">(${pageCount} Sayfa)</span>` : '';
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-md border text-[11px] font-semibold ${badgeClass}">${methodText}${pages}</span>`;
}

// Sonuç Gösterimi
function displayResults(data) {
    loader.classList.add('hidden');
    
    activeAnalysisData = data;
    currentSummaryOriginal = data.summary;
    currentSummaryTranslated = null;
    isShowingTranslation = false;

    const riskBadge = getRiskBadge(data.risk_level, data.risk_score);
    const methodBadge = getMethodBadge(data.extraction_method, data.page_count);
    const isTurkish = (data.language === 'tr');
    const langBadgeClass = isTurkish ? 'lang-badge-tr' : 'lang-badge-en';
    const langFlag = isTurkish ? '🇹🇷' : '🇬🇧';
    const langName = data.language_label || (isTurkish ? 'Türkçe' : 'English');
    const translateBtnText = isTurkish ? "🌐 English'e Çevir" : "🌐 Türkçe'ye Çevir";
    
    resultsDiv.innerHTML = `
        <!-- Üst Metot ve Durum Barı -->
        <div class="flex items-center justify-between px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
            <span class="text-slate-400 font-medium">İşlem Modeli & Okuma:</span>
            <div>${methodBadge}</div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <!-- 1. Belge Dili -->
            <div class="p-3.5 sm:p-4 rounded-xl glass-inner flex flex-col justify-between">
                <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Belge Dili</span>
                <div class="flex items-center gap-1.5 mt-0.5">
                    <span class="${langBadgeClass}">${langFlag} ${data.language ? data.language.toUpperCase() : 'TR'}</span>
                    <span class="text-sm sm:text-base font-bold text-slate-100">${langName}</span>
                </div>
            </div>

            <!-- 2. Belge Kategorisi -->
            <div class="p-3.5 sm:p-4 rounded-xl glass-inner flex flex-col justify-between">
                <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Belge Kategorisi</span>
                <p class="text-sm sm:text-base font-bold text-slate-100 mt-0.5 flex items-center gap-1.5">
                    📁 ${data.category}
                </p>
            </div>

            <!-- 3. Risk Değerlendirmesi -->
            <div class="p-3.5 sm:p-4 rounded-xl glass-inner flex flex-col justify-between">
                <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Güvenlik Riski</span>
                <div class="mt-0.5">${riskBadge}</div>
            </div>
        </div>

        <!-- Anahtar İfadeler -->
        <div class="p-3.5 sm:p-4 rounded-xl glass-inner">
            <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Anahtar İfadeler (Keywords)</span>
            <div class="flex flex-wrap gap-1.5 sm:gap-2">
                ${data.keywords && data.keywords.length > 0 
                    ? data.keywords.map(kw => `<span class="px-2.5 py-1 bg-slate-900/90 border border-slate-700/80 text-blue-300 rounded-lg text-xs font-semibold shadow-sm"># ${kw}</span>`).join('') 
                    : '<span class="text-slate-500 text-xs">Anahtar kelime bulunamadı.</span>'}
            </div>
        </div>

        <!-- Yapay Zekâ Özeti ve Çeviri Alanı -->
        <div class="p-4 sm:p-5 rounded-xl glass-inner relative border border-blue-500/20 shadow-md">
            <div class="flex flex-wrap justify-between items-center gap-2 mb-2.5">
                <div class="flex items-center gap-2">
                    <span class="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                        ✨ Yapay Zekâ Özeti
                    </span>
                    <span id="summary-lang-indicator" class="${langBadgeClass} text-[10px] py-0.5 px-1.5">${langName}</span>
                </div>
                
                <div class="flex items-center gap-1.5">
                    <!-- Çift Yönlü Çeviri Butonu -->
                    <button id="translate-btn" onclick="toggleSummaryTranslation()" class="text-xs text-slate-300 hover:text-white transition flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 font-semibold hover:border-blue-500">
                        ${translateBtnText}
                    </button>
                    <!-- Kopyalama Butonu -->
                    <button id="copy-btn" onclick="copySummary()" class="text-xs text-slate-300 hover:text-white transition flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 font-semibold">
                        📋 Kopyala
                    </button>
                </div>
            </div>
            <p id="summary-content" class="text-slate-100 leading-relaxed text-xs sm:text-sm md:text-base whitespace-pre-wrap font-normal">${data.summary}</p>
        </div>

        <!-- Yeni Analiz Butonu -->
        <button onclick="resetAnalysis()" class="w-full py-3 bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white rounded-xl font-bold text-xs sm:text-sm transition shadow-lg shadow-blue-600/30">
            ↺ Yeni Bir Analiz Yap
        </button>
    `;
    resultsDiv.classList.remove('hidden');
}
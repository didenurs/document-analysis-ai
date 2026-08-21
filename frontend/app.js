const tabPdf = document.getElementById('tab-pdf');
const tabText = document.getElementById('tab-text');
const tabPhase4 = document.getElementById('tab-phase4');
const pdfSection = document.getElementById('pdf-section');
const textSection = document.getElementById('text-section');
const phase4Section = document.getElementById('phase4-section');

const p4SubtabBatch = document.getElementById('p4-subtab-batch');
const p4SubtabCompare = document.getElementById('p4-subtab-compare');
const p4BatchView = document.getElementById('p4-batch-view');
const p4CompareView = document.getElementById('p4-compare-view');

const batchDropZone = document.getElementById('batch-drop-zone');
const batchFileInput = document.getElementById('batch-file-input');
const batchSelectedFilesList = document.getElementById('batch-selected-files-list');
const analyzeBatchBtn = document.getElementById('analyze-batch-btn');

const compareDoc1 = document.getElementById('compare-doc1');
const compareDoc2 = document.getElementById('compare-doc2');
const compareDocsBtn = document.getElementById('compare-docs-btn');

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

// HTML Karakterlerini Kaçırma (XSS Koruması)
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;

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
let p4Subtab = 'batch';
let selectedBatchFiles = [];

// Sekme Değiştirme
tabPdf.addEventListener('click', () => {
    activeTab = 'pdf';
    tabPdf.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-blue-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-2';
    tabText.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    tabPhase4.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    
    pdfSection.classList.remove('hidden');
    textSection.classList.add('hidden');
    phase4Section.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    hideToast();
});

tabText.addEventListener('click', () => {
    activeTab = 'text';
    tabText.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-blue-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-2';
    tabPdf.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    tabPhase4.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    
    textSection.classList.remove('hidden');
    pdfSection.classList.add('hidden');
    phase4Section.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    hideToast();
});

tabPhase4.addEventListener('click', () => {
    activeTab = 'phase4';
    tabPhase4.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-emerald-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-2';
    tabPdf.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    tabText.className = 'flex-1 py-2.5 px-3 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2';
    
    phase4Section.classList.remove('hidden');
    pdfSection.classList.add('hidden');
    textSection.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    hideToast();
});

// Faz 4 Alt Sekme Seçimi
p4SubtabBatch.addEventListener('click', () => {
    p4Subtab = 'batch';
    p4SubtabBatch.className = 'flex-1 py-2 rounded-md bg-emerald-600 text-white transition shadow';
    p4SubtabCompare.className = 'flex-1 py-2 rounded-md text-slate-400 hover:text-slate-200 transition';
    p4BatchView.classList.remove('hidden');
    p4CompareView.classList.add('hidden');
    resultsDiv.classList.add('hidden');
});

p4SubtabCompare.addEventListener('click', () => {
    p4Subtab = 'compare';
    p4SubtabCompare.className = 'flex-1 py-2 rounded-md bg-indigo-600 text-white transition shadow';
    p4SubtabBatch.className = 'flex-1 py-2 rounded-md text-slate-400 hover:text-slate-200 transition';
    p4CompareView.classList.remove('hidden');
    p4BatchView.classList.add('hidden');
    resultsDiv.classList.add('hidden');
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
    tr_cyber: "GİZLİ OLAY RAPORU: ACİL SALDIRI MÜDAHALESİ GEREKLİDİR Saat 02:00 sularında dahili izleme sistemlerimiz, merkezi kurumsal ağımızın birincil veritabanı güvenlik duvarında kritik bir arıza tespit etti. Son derece koordineli bir siber saldırı, bulut altyapımızda yeni keşfedilen bir sıfır gün güvenlik açığını başarıyla istismar ederek benzeri görülmemiş büyüklükte bir veri ihlaline yol açtı. Kötü niyetli saldırganlar ikincil kimlik doğrulama protokollerini ve şifreleme katmanlarını atlatmayı başararak müşterilerimizin son derece gizli finansal kayıtları için ciddi bir tehdit oluşturdu. Güvenliği ihlal edilen sunucular derhal izole edilip çevrimdışı bırakılmazsa büyük bir veri sızıntısının gerçekleşme olasılığı yüksek olduğundan, küresel olay müdahale ekibimiz tüm departmanlarda resmi olarak acil durum ilan etti. Tüm sistem yöneticilerinin, geliştiricilerin ve personelin kimlik bilgilerini sıfırlaması ve tespit edilen güvenlik açığını bir saat içinde yamaması kesinlikle ve acilen gerekmektedir. Bu ihlal, operasyonel bütünlüğümüz ve pazar itibarımız için kritik bir tehdit oluşturmaktadır. Saldırının tam kapsamını anlamak ve gelecekte başka bir saldırıyı veya yıkıcı sistem çökmesini önlemek amacıyla acil bir güvenlik denetimi ve adli bilişim analizi yürütülmektedir.",
    tr_kvkk: "MÜŞTERİ HESAP EKSTRESİ VE GİZLİ BİLDİRİM:\nSayın Ahmet Yılmaz, 10000000146 T.C. Kimlik numaranıza ait TR12 3456 7890 1234 5678 9012 34 IBAN numaralı hesabınızdan 4543-1234-5678-9012 numaralı kredi kartınıza ödeme yapılmıştır. Detaylı bilgi için müşteri temsilciniz ile ahmet.yilmaz@kurumsal.com veya 0532 123 45 67 üzerinden iletişime geçebilirsiniz. Güvenlik bağlantı IP adresi: 192.168.1.105.",
    tr_finance: "Üçüncü Çeyrek Finansal Raporu: Şirketimiz bulut ve yapay zekâ yazılım ürünlerine olan yüksek talep sayesinde faaliyet gelirlerinde %28 oranında rekor büyüme kaydetti. İşletme giderleri %6 oranında azalırken net kâr marjı güçlendi ve serbest nakit akışı genişledi.",
    tr_short: "Bugün üniversitede yapay zekâ ve derin öğrenme modelleri üzerine kapsamlı bir ders işlendi.",
    
    en_cyber: "CONFIDENTIAL INCIDENT REPORT: IMMEDIATE ATTACK RESPONSE REQUIRED At 02:00 AM standard time, our internal monitoring systems detected a critical failure in the primary database firewall of our central corporate network. A highly coordinated cyber attack successfully exploited a newly discovered zero-day vulnerability in our cloud infrastructure, leading to a massive and unprecedented data breach. The malicious actors managed to bypass the secondary authentication protocols and encryption layers, posing a severe threat to our clients' highly confidential financial records. Our global incident response team has officially declared a state of emergency across all departments, as there is a high probability of an imminent data leak if the compromised servers are not isolated and taken offline immediately. It is absolutely urgent that all system administrators, developers, and staff reset their credentials and patch the identified vulnerability within the next hour. This breach represents a critical threat to our operational integrity and overall market reputation. An urgent security audit and forensic analysis are currently underway to understand the full scope of the intrusion and to prevent any further attack or catastrophic system failure in the near future.",
    en_kvkk: "EMPLOYEE CONFIDENTIAL RECORD:\nEmployee Dr. John Watson with SSN 123-45-6789 and company email john.watson@enterprise.com has been assigned internal server IP 10.0.0.45. Emergency phone contact is +1 (555) 234-5678. Corporate card: 4111-2222-3333-4444.",
    en_finance: "Quarterly Financial Overview: The company achieved a record 24% growth in operating revenue driven by strong enterprise software adoption. Operating expenses decreased by 8%, resulting in improved net profit margins and sustainable free cash flow expansion.",
    en_short: "FastAPI is a modern, high-performance web framework for building APIs with Python."
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

// --- FAZ 5: CANLI METRİKLER, ANOMALİ & WEBHOOK ---

async function openMetricsModal() {
    const modal = document.getElementById('metrics-modal');
    modal.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/metrics`);
        const data = await parseApiResponse(response);

        document.getElementById('metric-total').textContent = data.total_processed || 0;
        document.getElementById('metric-pii').textContent = data.total_pii_masked || 0;
        document.getElementById('metric-avg-risk').textContent = data.avg_risk_score || 0.0;
    } catch (err) {
        console.warn("Metrikler alınamadı:", err);
    }
}
window.openMetricsModal = openMetricsModal;

function closeMetricsModal() {
    document.getElementById('metrics-modal').classList.add('hidden');
}
window.closeMetricsModal = closeMetricsModal;

async function sendTestWebhook() {
    const urlInput = document.getElementById('webhook-url-input');
    const msgEl = document.getElementById('webhook-status-msg');
    const url = urlInput.value.trim();

    if (!url) {
        showToast("Lütfen bir Webhook URL adresi girin.", "warning");
        return;
    }

    msgEl.classList.remove('hidden', 'text-emerald-400', 'text-rose-400');
    msgEl.textContent = "İletiliyor...";

    try {
        const response = await fetch(`${API_URL}/webhooks/test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ webhook_url: url, event_type: "risk.critical" })
        });

        const data = await parseApiResponse(response);
        if (data.success) {
            msgEl.className = "text-[11px] font-mono text-emerald-400 block";
            msgEl.textContent = `✅ ${data.message}`;
            showToast("Webhook testi başarıyla iletildi!", "success");
        } else {
            msgEl.className = "text-[11px] font-mono text-rose-400 block";
            msgEl.textContent = `❌ ${data.message}`;
        }
    } catch (err) {
        msgEl.className = "text-[11px] font-mono text-rose-400 block";
        msgEl.textContent = `❌ Hata: ${err.message}`;
    }
}
window.sendTestWebhook = sendTestWebhook;

// --- FAZ 4: TOPLU ANALİZ, KARŞILAŞTIRMA & EXPORT ---

// Faz 4 Çoklu Dosya Seçimi / Drag-Drop
batchDropZone.addEventListener('click', () => batchFileInput.click());

batchDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    batchDropZone.classList.add('border-emerald-400', 'bg-emerald-950/30');
});

batchDropZone.addEventListener('dragleave', () => {
    batchDropZone.classList.remove('border-emerald-400', 'bg-emerald-950/30');
});

batchDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    batchDropZone.classList.remove('border-emerald-400', 'bg-emerald-950/30');
    if (e.dataTransfer.files.length > 0) {
        handleBatchFiles(Array.from(e.dataTransfer.files));
    }
});

batchFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleBatchFiles(Array.from(e.target.files));
    }
});

function handleBatchFiles(files) {
    selectedBatchFiles = files;
    if (files.length === 0) {
        batchSelectedFilesList.classList.add('hidden');
        return;
    }
    
    batchSelectedFilesList.innerHTML = `
        <div class="font-bold text-emerald-400 mb-1">Seçilen Dokümanlar (${files.length} Adet):</div>
        <div class="space-y-1">
            ${files.map((f, idx) => `<div class="flex justify-between font-mono text-[11px]"><span>📄 ${escapeHtml(f.name)}</span><span class="text-slate-500">${(f.size / 1024).toFixed(1)} KB</span></div>`).join('')}
        </div>
    `;
    batchSelectedFilesList.classList.remove('hidden');
}

analyzeBatchBtn.addEventListener('click', async () => {
    if (!selectedBatchFiles || selectedBatchFiles.length === 0) {
        showToast("Lütfen toplu analiz için en az 1 adet dosya seçin.", "warning");
        return;
    }
    
    setLoading(true);
    if (loaderTitle) loaderTitle.textContent = "Toplu Doküman Analizi Yapılıyor";
    if (loaderSubtext) loaderSubtext.textContent = `${selectedBatchFiles.length} adet doküman sırayla ayrıştırılıyor, özetleniyor ve birleşik risk haritası oluşturuluyor...`;
    hideToast();

    const formData = new FormData();
    for (const file of selectedBatchFiles) {
        formData.append("files", file);
    }

    try {
        const response = await fetch(`${API_URL}/analyze-batch`, {
            method: "POST",
            body: formData
        });

        const data = await parseApiResponse(response);
        displayBatchResults(data);
    } catch (error) {
        showToast(error.message, "error");
        setLoading(false);
    }
});

// Karşılaştırma Çalıştırıcı
compareDocsBtn.addEventListener('click', async () => {
    const doc1 = compareDoc1.value.trim();
    const doc2 = compareDoc2.value.trim();

    if (!doc1 || !doc2) {
        showToast("Lütfen karşılaştırma için her iki doküman kutusuna da metin girin.", "warning");
        return;
    }

    setLoading(true);
    if (loaderTitle) loaderTitle.textContent = "Dokümanlar Karşılaştırılıyor";
    if (loaderSubtext) loaderSubtext.textContent = "Semantik benzerlik, risk farkı, eklenen/çıkarılan ifadeler ve KVKK sızıntı değişimi hesaplanıyor...";
    hideToast();

    try {
        const response = await fetch(`${API_URL}/compare-documents`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                doc1_text: doc1,
                doc2_text: doc2,
                doc1_title: "Doküman 1 (Eski)",
                doc2_title: "Doküman 2 (Yeni)"
            })
        });

        const data = await parseApiResponse(response);
        displayCompareResults(data);
    } catch (error) {
        showToast(error.message, "error");
        setLoading(false);
    }
});

function loadCompareSample() {
    compareDoc1.value = "HİZMET SÖZLEŞMESİ\nMadde 1: Taraflar arasında bulut yazılım hizmeti sağlanacaktır.\nMadde 2: Yıllık hizmet bedeli 50.000 TL olup ödemeler aylık yapılacaktır.\nMadde 3: Veri güvenliği ihlallerinde yüklenici firma 100.000 TL tazminat ödemeyi taahhüt eder.\nİletişim: destek@firmamiz.com - 0212 555 0000";
    compareDoc2.value = "HİZMET SÖZLEŞMESİ (REVİZE V2)\nMadde 1: Taraflar arasında bulut yazılım ve yapay zekâ altyapı hizmeti sağlanacaktır.\nMadde 2: Yıllık hizmet bedeli 85.000 TL olup ödemeler 3 aylık periyotlarla yapılacaktır.\nMadde 3: Veri ihlali durumunda yüklenici firma 500.000 TL ceza ve KVKK tazminatı üstlenir.\nMadde 4: Yetkili mahkeme İstanbul Çağlayan Mahkemeleridir.\nHassas Kayıt: TCKN 12345678901, IP: 192.168.1.50";
    showToast("Örnek karşılaştırma metinleri yüklendi.", "success");
}
window.loadCompareSample = loadCompareSample;

// Export İndirme Fonksiyonu
async function downloadExport(format) {
    if (!activeAnalysisData) {
        showToast("İndirilecek aktif analiz verisi bulunamadı.", "warning");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/export/${format}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                analysis_data: activeAnalysisData,
                export_format: format
            })
        });

        if (!response.ok) throw new Error("Rapor indirilirken sunucu hatası oluştu.");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `doc_analysis_report.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

        showToast(`Analiz raporu .${format.toUpperCase()} olarak indirildi!`, "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}
window.downloadExport = downloadExport;

// Dosya Seçme / Drag-Drop (Tekil)
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
        if (loaderSubtext) loaderSubtext.textContent = "AI Vision & OCR motoru ile görseldeki metinler okunuyor, KVKK ve risk analizi yapılıyor...";
    } else {
        if (loaderTitle) loaderTitle.textContent = "Yapay Zekâ Analiz Ediyor";
        if (loaderSubtext) loaderSubtext.textContent = "PDF ayrıştırılıyor, taranmış sayfalar OCR ile taranıyor, KVKK maskelemesi ve özet çıkarılıyor...";
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
    if (loaderSubtext) loaderSubtext.textContent = "Groq LLaMA-3.3, KVKK maskeleme ve çok dilli risk analizi yapılıyor...";
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
    activeDocumentText = "";
    currentSummaryOriginal = "";
    currentSummaryTranslated = null;
    isShowingTranslation = false;
    isShowingMasked = true;
    chatHistory = [];
    isChatSending = false;
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

// Maskeli / Orijinal Metin Gösterim Toggle'ı
function toggleMaskedTextView() {
    const textDisplayEl = document.getElementById('document-text-content');
    const toggleBtn = document.getElementById('toggle-mask-btn');
    if (!textDisplayEl || !toggleBtn || !activeAnalysisData) return;

    if (isShowingMasked) {
        // Orijinal metni göster
        textDisplayEl.textContent = activeAnalysisData.cleaned_text || activeDocumentText;
        isShowingMasked = false;
        toggleBtn.innerHTML = '🔒 Maskeli Görünüme Geç';
        toggleBtn.classList.remove('bg-amber-500/20', 'border-amber-500/40', 'text-amber-300');
        toggleBtn.classList.add('bg-slate-900', 'border-slate-700', 'text-slate-300');
    } else {
        // Maskeli metni göster
        textDisplayEl.textContent = activeAnalysisData.masked_text || activeAnalysisData.cleaned_text || activeDocumentText;
        isShowingMasked = true;
        toggleBtn.innerHTML = '👁️ Orijinal Metni Gör';
        toggleBtn.classList.add('bg-amber-500/20', 'border-amber-500/40', 'text-amber-300');
        toggleBtn.classList.remove('bg-slate-900', 'border-slate-700', 'text-slate-300');
    }
}
window.toggleMaskedTextView = toggleMaskedTextView;

// Maskelenmiş Metni Kopyalama
function copyMaskedDocument() {
    const maskedText = activeAnalysisData?.masked_text || document.getElementById('document-text-content')?.innerText || '';
    if (maskedText) {
        navigator.clipboard.writeText(maskedText).then(() => {
            const btn = document.getElementById('copy-masked-btn');
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
window.copyMaskedDocument = copyMaskedDocument;

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

// RAG Doküman Sohbet Fonksiyonları
async function sendChatMessage(customQuestion = null) {
    if (isChatSending) return;
    
    const inputEl = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const question = (customQuestion || inputEl?.value || '').trim();
    if (!question) return;

    if (!activeDocumentText) {
        showToast("Sohbet edebilmek için önce bir doküman analiz edilmelidir.", "warning");
        return;
    }

    if (inputEl) inputEl.value = '';
    isChatSending = true;

    // 1. Kullanıcı Mesajını Ekrana Ekle
    const userMsgHtml = `
        <div class="flex justify-end animate-fade-in">
            <div class="max-w-[85%] sm:max-w-[75%] p-3 rounded-2xl chat-bubble-user text-xs sm:text-sm font-medium shadow-md">
                ${escapeHtml(question)}
            </div>
        </div>
    `;
    messagesContainer.insertAdjacentHTML('beforeend', userMsgHtml);

    // 2. Yükleniyor / Yazıyor Baloncuğu
    const typingId = `typing-${Date.now()}`;
    const typingHtml = `
        <div id="${typingId}" class="flex items-start gap-2 animate-fade-in">
            <div class="w-7 h-7 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs shrink-0 mt-0.5">
                🤖
            </div>
            <div class="max-w-[85%] sm:max-w-[75%] p-3 rounded-2xl chat-bubble-ai text-xs sm:text-sm text-slate-300 shadow-md flex items-center gap-2">
                <span class="inline-block w-2 h-2 rounded-full bg-blue-400 animate-ping"></span>
                <span>Doküman taranıyor ve yanıt üretiliyor...</span>
            </div>
        </div>
    `;
    messagesContainer.insertAdjacentHTML('beforeend', typingHtml);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/chat-document`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                document_text: activeDocumentText,
                question: question,
                history: chatHistory,
                language: activeAnalysisData?.language || 'tr'
            })
        });

        const data = await parseApiResponse(response);
        
        // Typing animasyonunu kaldır
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        // 3. AI Cevabını Ekrana Ekle
        const confidenceBadge = data.confidence 
            ? `<span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-semibold">🎯 %${Math.round(data.confidence * 100)} Doğruluk</span>` 
            : '';

        let sourcesHtml = '';
        if (data.sources && data.sources.length > 0) {
            const sourceItems = data.sources.map((s, idx) => `
                <div class="p-2 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 leading-relaxed font-mono">
                    <span class="text-blue-400 font-bold">#${idx+1}:</span> "${escapeHtml(s.slice(0, 180))}${s.length > 180 ? '...' : ''}"
                </div>
            `).join('');

            sourcesHtml = `
                <details class="mt-2.5 pt-2 border-t border-slate-800/80 text-[11px]">
                    <summary class="cursor-pointer text-slate-400 hover:text-blue-400 font-semibold select-none flex items-center gap-1">
                        <span>📄 İlgili Kaynak Pasajları Göster (${data.sources.length})</span>
                    </summary>
                    <div class="mt-2 space-y-1.5 animate-fade-in">
                        ${sourceItems}
                    </div>
                </details>
            `;
        }

        const aiMsgHtml = `
            <div class="flex items-start gap-2 animate-fade-in">
                <div class="w-7 h-7 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs shrink-0 mt-0.5">
                    🤖
                </div>
                <div class="max-w-[85%] sm:max-w-[80%] p-3.5 rounded-2xl chat-bubble-ai text-xs sm:text-sm text-slate-100 shadow-md">
                    <div class="flex items-center justify-between gap-2 mb-1.5">
                        <span class="font-bold text-blue-400 text-[11px]">Doc Assistant AI</span>
                        ${confidenceBadge}
                    </div>
                    <div class="leading-relaxed whitespace-pre-wrap">${escapeHtml(data.answer)}</div>
                    ${sourcesHtml}
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', aiMsgHtml);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Geçmişe ekle
        chatHistory.push({ role: "user", content: question });
        chatHistory.push({ role: "assistant", content: data.answer });

    } catch (err) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        const errorMsgHtml = `
            <div class="flex items-start gap-2 animate-fade-in">
                <div class="w-7 h-7 rounded-xl bg-rose-600/20 border border-rose-500/30 flex items-center justify-center text-rose-400 text-xs shrink-0 mt-0.5">
                    ⚠️
                </div>
                <div class="p-3 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs sm:text-sm">
                    Soru yanıtlanırken bir hata oluştu: ${escapeHtml(err.message)}
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', errorMsgHtml);
    } finally {
        isChatSending = false;
    }
}
window.sendChatMessage = sendChatMessage;

function askSuggestedQuestion(q) {
    sendChatMessage(q);
}
window.askSuggestedQuestion = askSuggestedQuestion;

// HTML Kaçış Yardımcısı
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Sonuç Gösterimi
function displayResults(data) {
    loader.classList.add('hidden');
    
    activeAnalysisData = data;
    activeDocumentText = data.cleaned_text || textInput.value || data.summary || "";
    currentSummaryOriginal = data.summary;
    currentSummaryTranslated = null;
    isShowingTranslation = false;
    isShowingMasked = true;
    chatHistory = [];

    const riskBadge = getRiskBadge(data.risk_level, data.risk_score);
    const methodBadge = getMethodBadge(data.extraction_method, data.page_count);
    const isTurkish = (data.language === 'tr');
    const langBadgeClass = isTurkish ? 'lang-badge-tr' : 'lang-badge-en';
    const langFlag = isTurkish ? '🇹🇷' : '🇬🇧';
    const langName = data.language_label || (isTurkish ? 'Türkçe' : 'English');
    const translateBtnText = isTurkish ? "🌐 English'e Çevir" : "🌐 Türkçe'ye Çevir";
    
    // KVKK Raporu Bilgileri
    const kvkkReport = data.kvkk_report || { status: '🛡️ Güvenli', risk_level: 'Low', total_entities: 0, breakdown: {} };
    const entities = data.entities || [];
    
    let kvkkStatusBadgeClass = 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300';
    if (kvkkReport.risk_level === 'High') {
        kvkkStatusBadgeClass = 'bg-rose-500/15 border-rose-500/40 text-rose-300';
    } else if (kvkkReport.risk_level === 'Medium') {
        kvkkStatusBadgeClass = 'bg-amber-500/15 border-amber-500/40 text-amber-300';
    }

    // Varlık Rozetleri
    let entityBadgesHtml = '';
    if (entities.length > 0) {
        const typeLabels = {
            'TCKN': '🪪 TCKN',
            'EMAIL': '📧 E-posta',
            'PHONE': '📞 Telefon',
            'IBAN': '🏦 IBAN',
            'CREDIT_CARD': '💳 Kredi Kartı',
            'IP_ADDRESS': '🌐 IP Adresi',
            'NAME': '👤 Kişi Adı',
            'API_KEY': '🔑 API Key'
        };

        const breakdown = kvkkReport.breakdown || {};
        entityBadgesHtml = Object.entries(breakdown).map(([type, count]) => {
            const label = typeLabels[type] || type;
            return `<span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700 text-slate-300 text-[11px] font-semibold">${label}: <b>${count}</b></span>`;
        }).join(' ');
    } else {
        entityBadgesHtml = '<span class="text-slate-500 text-xs">Kişisel veya hassas veri bulunamadı.</span>';
    }

    // Hızlı Soru Önerileri (Dile göre dinamik)
    const suggestedChips = isTurkish ? `
        <button type="button" onclick="askSuggestedQuestion('Bu belgedeki en kritik bulgu veya olay nedir?')" class="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/60 hover:text-blue-300 text-[11px] font-medium text-slate-300 transition text-left">
            ⚡ En kritik bulgu nedir?
        </button>
        <button type="button" onclick="askSuggestedQuestion('Alınması gereken acil aksiyonlar ve önlemler nelerdir?')" class="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/60 hover:text-blue-300 text-[11px] font-medium text-slate-300 transition text-left">
            🛡️ Acil aksiyonlar nelerdir?
        </button>
        <button type="button" onclick="askSuggestedQuestion('Dokümanda belirtilen önemli tarihler ve sayılar neler?')" class="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/60 hover:text-blue-300 text-[11px] font-medium text-slate-300 transition text-left">
            📅 Tarihler ve sayılar neler?
        </button>
    ` : `
        <button type="button" onclick="askSuggestedQuestion('What is the most critical incident or finding in this document?')" class="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/60 hover:text-blue-300 text-[11px] font-medium text-slate-300 transition text-left">
            ⚡ What are the key findings?
        </button>
        <button type="button" onclick="askSuggestedQuestion('What urgent actions or mitigation steps are required?')" class="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/60 hover:text-blue-300 text-[11px] font-medium text-slate-300 transition text-left">
            🛡️ What actions are needed?
        </button>
        <button type="button" onclick="askSuggestedQuestion('What are the key dates, figures, and metrics mentioned?')" class="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/60 hover:text-blue-300 text-[11px] font-medium text-slate-300 transition text-left">
            📅 What are key figures & dates?
        </button>
    `;

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

        <!-- FAZ 3: KVKK / GDPR & Kişisel Veri Maskeleme Paneli -->
        <div class="p-4 rounded-xl glass-inner border border-emerald-500/30 shadow-md space-y-2.5">
            <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <span class="text-base">🛡️</span>
                    <span class="text-xs font-bold text-white uppercase tracking-wider">KVKK / GDPR & Veri Maskeleme Raporu</span>
                </div>
                <span class="px-2.5 py-1 rounded-lg border text-xs font-bold ${kvkkStatusBadgeClass}">
                    ${kvkkReport.status}
                </span>
            </div>

            <!-- Tespit Edilen Varlık Dağılımı -->
            <div class="flex flex-wrap gap-1.5 pt-1">
                ${entityBadgesHtml}
            </div>

            <!-- Maskelenmiş Metin Görüntüleme & Kontroller -->
            <div class="mt-2 pt-2 border-t border-slate-800/80">
                <div class="flex items-center justify-between gap-2 mb-1.5">
                    <span class="text-[11px] font-semibold text-slate-400">Doküman Metni (Hassas Veriler Koruma Altında):</span>
                    <div class="flex items-center gap-1.5">
                        <button id="toggle-mask-btn" onclick="toggleMaskedTextView()" class="text-[11px] text-amber-300 bg-amber-500/20 border border-amber-500/40 hover:bg-amber-500/30 transition px-2.5 py-0.5 rounded-md font-semibold">
                            👁️ Orijinal Metni Gör
                        </button>
                        <button id="copy-masked-btn" onclick="copyMaskedDocument()" class="text-[11px] text-slate-300 bg-slate-900 border border-slate-700 hover:text-white transition px-2 py-0.5 rounded-md font-semibold">
                            📋 Maskeli Metni Kopyala
                        </button>
                    </div>
                </div>
                <div id="document-text-content" class="p-3 max-h-[140px] overflow-y-auto chat-scroll rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 leading-relaxed font-mono whitespace-pre-wrap select-all">
                    ${escapeHtml(data.masked_text || data.cleaned_text || activeDocumentText)}
                </div>
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

        <!-- FAZ 5: Anomali & Sahtecilik Tespiti Kartı -->
        ${(data.anomaly_report && data.anomaly_report.has_anomaly) ? `
        <div class="p-4 rounded-xl glass-inner border border-rose-500/40 shadow-md space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <span class="text-base">🚨</span>
                    <span class="text-xs font-bold text-rose-400 uppercase tracking-wider">Anomali & Manipülasyon Şüphesi (Faz 5)</span>
                </div>
                <span class="px-2.5 py-0.5 rounded bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/40">Anomali Skoru: ${data.anomaly_report.anomaly_score}/100</span>
            </div>
            <p class="text-xs text-slate-200 leading-relaxed font-semibold">${escapeHtml(data.anomaly_report.details)}</p>
            <div class="flex flex-wrap gap-1.5 pt-1">
                ${(data.anomaly_report.anomaly_flags || []).map(f => `<span class="px-2 py-0.5 rounded bg-rose-950 border border-rose-700 text-rose-300 text-[11px] font-semibold">${escapeHtml(f)}</span>`).join(' ')}
            </div>
        </div>
        ` : ''}

        <!-- FAZ 5: Otomatik Aksiyon Önerileri Motoru (Checklist) -->
        ${(data.recommendations && data.recommendations.length > 0) ? `
        <div class="p-4 rounded-xl glass-inner border border-blue-500/30 shadow-md space-y-2.5">
            <div class="flex items-center gap-2">
                <span class="text-base">📋</span>
                <span class="text-xs font-bold text-blue-400 uppercase tracking-wider">Yapay Zekâ Aksiyon Önerileri (Faz 5 Checklist)</span>
            </div>
            <div class="space-y-2">
                ${data.recommendations.map(rec => {
                    let badge = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40';
                    if (rec.priority === 'High') badge = 'bg-rose-500/15 text-rose-300 border-rose-500/40';
                    else if (rec.priority === 'Medium') badge = 'bg-amber-500/15 text-amber-300 border-amber-500/40';

                    return `
                        <label class="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 cursor-pointer hover:border-slate-700 transition">
                            <input type="checkbox" class="mt-1 rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-emerald-500/40">
                            <div class="flex-1 space-y-0.5">
                                <div class="flex items-center justify-between gap-2">
                                    <span class="font-bold text-slate-100 text-xs">${escapeHtml(rec.title)}</span>
                                    <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${badge}">${rec.priority}</span>
                                </div>
                                <p class="text-[11px] text-slate-400 leading-relaxed">${escapeHtml(rec.description)}</p>
                            </div>
                        </label>
                    `;
                }).join('')}
            </div>
        </div>
        ` : ''}


        <!-- FAZ 2: Doküman ile Sohbet (RAG Q&A) Paneli -->
        <div class="p-4 sm:p-5 rounded-2xl glass-inner border border-indigo-500/30 shadow-xl space-y-3.5">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="text-base sm:text-lg">💬</span>
                    <div>
                        <h3 class="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                            Dokümanla Sohbet Et (RAG Q&A)
                            <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">Groq LLaMA-3.3</span>
                        </h3>
                        <p class="text-[11px] text-slate-400">Bu dokümanın içeriğine dair her şeyi sorun; yapay zekâ kaynak referanslarıyla yanıtlasın.</p>
                    </div>
                </div>
            </div>

            <!-- Hızlı Soru Çipleri -->
            <div class="flex flex-wrap gap-1.5 pt-1">
                ${suggestedChips}
            </div>

            <!-- Mesaj Listesi -->
            <div id="chat-messages" class="max-h-[280px] overflow-y-auto chat-scroll p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-3">
                <div class="flex items-start gap-2">
                    <div class="w-7 h-7 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs shrink-0 mt-0.5">
                        🤖
                    </div>
                    <div class="max-w-[85%] p-3 rounded-2xl chat-bubble-ai text-xs sm:text-sm text-slate-200">
                        ${isTurkish 
                            ? 'Merhaba! Bu dokümanı analiz ettim. İçerikte geçen herhangi bir detay, tarih, kişi veya aksiyon hakkında soru sorabilirsiniz.' 
                            : 'Hello! I have analyzed this document. You can ask any specific questions about dates, facts, figures, or action items.'}
                    </div>
                </div>
            </div>

            <!-- Soru Giriş Alanı -->
            <form id="chat-form" onsubmit="event.preventDefault(); sendChatMessage();" class="flex gap-2">
                <input 
                    type="text" 
                    id="chat-input" 
                    placeholder="${isTurkish ? 'Doküman hakkında bir soru sorun (örn. Olay saat kaçta gerçekleşti?)...' : 'Ask a question about this document...'}" 
                    class="flex-1 px-3.5 py-2.5 bg-slate-950/90 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                    autocomplete="off"
                >
                <button 
                    type="submit" 
                    id="chat-send-btn" 
                    class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:scale-[0.98] text-white rounded-xl text-xs sm:text-sm font-bold transition shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 shrink-0"
                >
                    <span>Gönder</span>
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </button>
            </form>
        </div>

        <!-- FAZ 4: Rapor Dışa Aktarma (Export) Paneli -->
        <div class="p-3.5 rounded-xl glass-inner border border-emerald-500/30 flex flex-wrap items-center justify-between gap-2 shadow font-sans">
            <div class="flex items-center gap-2">
                <span class="text-base">📥</span>
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Raporu Dışa Aktar (Faz 4 Export)</span>
            </div>
            <div class="flex items-center gap-1.5">
                <button type="button" onclick="downloadExport('json')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-slate-200 rounded-lg transition">
                    JSON
                </button>
                <button type="button" onclick="downloadExport('csv')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-emerald-300 rounded-lg transition">
                    📊 CSV
                </button>
                <button type="button" onclick="downloadExport('html')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white rounded-lg transition shadow">
                    📄 HTML / PDF Rapor
                </button>
            </div>
        </div>

        <!-- Yeni Analiz Butonu -->
        <button onclick="resetAnalysis()" class="w-full py-3 bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white rounded-xl font-bold text-xs sm:text-sm transition shadow-lg shadow-blue-600/30">
            ↺ Yeni Bir Doküman Analiz Et
        </button>
    `;
    resultsDiv.classList.remove('hidden');
}

// --- FAZ 4 TOPLU ANALİZ VE KARŞILAŞTIRMA SONUÇLARI ---

function displayBatchResults(data) {
    loader.classList.add('hidden');
    activeAnalysisData = data;
    
    const globalRiskBadge = getRiskBadge(data.global_risk_level, data.global_risk_score);
    const kvkk = data.global_kvkk_report || {};

    let docCardsHtml = '';
    (data.documents || []).forEach((docItem, idx) => {
        const a = docItem.analysis || {};
        const rBadge = getRiskBadge(a.risk_level, a.risk_score);
        docCardsHtml += `
            <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-200 text-xs sm:text-sm">📄 ${idx+1}. ${escapeHtml(docItem.filename)}</span>
                    <div>${rBadge}</div>
                </div>
                <div class="flex items-center gap-2 text-[11px] text-slate-400">
                    <span>📁 Kategori: <b>${a.category}</b></span>
                    <span>•</span>
                    <span>🌐 Dil: <b>${a.language_label || a.language}</b></span>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed font-normal">${escapeHtml(a.summary)}</p>
            </div>
        `;
    });

    resultsDiv.innerHTML = `
        <div class="p-4 rounded-2xl glass-inner border border-emerald-500/40 shadow-xl space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                    <h2 class="text-base font-bold text-emerald-400 flex items-center gap-2">
                        📦 Toplu Doküman Analiz Raporu (Faz 4)
                    </h2>
                    <p class="text-xs text-slate-400">Toplam ${data.total_documents} adet doküman işlendi ve birleşik rapor oluşturuldu.</p>
                </div>
                <div class="flex gap-1.5">
                    <button type="button" onclick="downloadExport('json')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-slate-200 rounded-lg">JSON</button>
                    <button type="button" onclick="downloadExport('csv')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-emerald-300 rounded-lg">📊 CSV</button>
                    <button type="button" onclick="downloadExport('html')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white rounded-lg">📄 HTML Rapor</button>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Genel Güvenlik Riski</span>
                    <div>${globalRiskBadge}</div>
                </div>
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Genel KVKK / PII Durumu</span>
                    <p class="text-xs font-bold text-emerald-300 mt-1">🛡️ ${kvkk.status || 'GÜVENLİ'} (Toplam ${kvkk.total_entities || 0} Varlık)</p>
                </div>
            </div>

            <div class="p-4 rounded-xl bg-slate-950/90 border border-emerald-500/20 space-y-1.5">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider block">✨ Genel Birleşik Özet</span>
                <p class="text-xs sm:text-sm text-slate-100 leading-relaxed">${escapeHtml(data.overall_summary)}</p>
            </div>

            <div class="space-y-2">
                <span class="text-xs font-bold text-slate-300 uppercase tracking-wider block">📂 Doküman Bazlı Analizler</span>
                <div class="space-y-2.5">${docCardsHtml}</div>
            </div>
        </div>

        <button onclick="resetAnalysis()" class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold text-xs sm:text-sm transition">
            ↺ Yeni Bir Analiz Yap
        </button>
    `;
    resultsDiv.classList.remove('hidden');
}

function displayCompareResults(data) {
    loader.classList.add('hidden');
    
    let simColor = 'text-emerald-400';
    if (data.similarity_percentage < 50) simColor = 'text-rose-400';
    else if (data.similarity_percentage < 80) simColor = 'text-amber-400';

    let addedHtml = (data.added_keypoints || []).map(s => `<li class="text-emerald-300">+ ${escapeHtml(s)}</li>`).join('');
    let removedHtml = (data.removed_keypoints || []).map(s => `<li class="text-rose-300">- ${escapeHtml(s)}</li>`).join('');

    resultsDiv.innerHTML = `
        <div class="p-4 sm:p-5 rounded-2xl glass-inner border border-indigo-500/40 shadow-xl space-y-4">
            <div class="border-b border-slate-800 pb-2">
                <h2 class="text-base font-bold text-indigo-400 flex items-center gap-2">
                    ⚖️ Doküman Karşılaştırma & Diff Raporu (Faz 4)
                </h2>
                <p class="text-xs text-slate-400">İki doküman arasındaki semantik benzerlik, risk değişimi ve içerik farkları aşağıdadır.</p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">İçerik Benzerliği</span>
                    <span class="text-2xl font-black ${simColor}">%${data.similarity_percentage}</span>
                </div>
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Risk Skoru Değişimi</span>
                    <span class="text-xs font-bold text-slate-200 block mt-1">${data.doc1_risk_score} ➔ ${data.doc2_risk_score}</span>
                    <span class="text-[11px] font-semibold text-amber-300 block mt-0.5">${escapeHtml(data.risk_status)}</span>
                </div>
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Hassas Veri (PII) Farkı</span>
                    <span class="text-lg font-bold text-indigo-300 block mt-1">${data.pii_diff_count >= 0 ? '+' : ''}${data.pii_diff_count} Varlık</span>
                </div>
            </div>

            <div class="p-3.5 rounded-xl bg-slate-950/90 border border-indigo-500/20">
                <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">📝 Karşılaştırma Özeti</span>
                <p class="text-xs sm:text-sm text-slate-200 leading-relaxed">${escapeHtml(data.summary_comparison)}</p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div class="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-1.5">
                    <span class="font-bold text-emerald-400 block">🟢 Eklenen Yeni İfadeler / Maddeler:</span>
                    <ul class="space-y-1 font-mono text-[11px]">${addedHtml || '<span class="text-slate-500">Yeni madde eklenmedi.</span>'}</ul>
                </div>
                <div class="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 space-y-1.5">
                    <span class="font-bold text-rose-400 block">🔴 Çıkarılan / Değişen İfadeler:</span>
                    <ul class="space-y-1 font-mono text-[11px]">${removedHtml || '<span class="text-slate-500">Çıkarılan madde yok.</span>'}</ul>
                </div>
            </div>
        </div>

        <button onclick="resetAnalysis()" class="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-xs sm:text-sm transition">
            ↺ Yeni Karşılaştırma Yap
        </button>
    `;
    resultsDiv.classList.remove('hidden');
}
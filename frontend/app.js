// DOM Elemanları
const tabPdf = document.getElementById('tab-pdf');
const tabKvkk = document.getElementById('tab-kvkk');
const tabText = document.getElementById('tab-text');
const tabCompare = document.getElementById('tab-compare') || document.getElementById('tab-phase4');

const pdfSection = document.getElementById('pdf-section');
const kvkkSection = document.getElementById('kvkk-section');
const textSection = document.getElementById('text-section');
const compareSection = document.getElementById('phase4-section');

const compareDoc1 = document.getElementById('compare-doc1');
const compareDoc2 = document.getElementById('compare-doc2');
const compareDocsBtn = document.getElementById('compare-docs-btn');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const selectedFilesContainer = document.getElementById('selected-files-container');
const analyzeFileBtn = document.getElementById('analyze-file-btn');

const kvkkDropZone = document.getElementById('kvkk-drop-zone');
const kvkkFileInput = document.getElementById('kvkk-file-input');
const kvkkSelectedFile = document.getElementById('kvkk-selected-file');
const kvkkTextInput = document.getElementById('kvkk-text-input');
const analyzeKvkkBtn = document.getElementById('analyze-kvkk-btn');
const clearKvkkTextBtn = document.getElementById('clear-kvkk-text-btn');
const kvkkCharCount = document.getElementById('kvkk-char-count');

const textInput = document.getElementById('text-input');
const analyzeTextBtn = document.getElementById('analyze-text-btn');
const clearTextBtn = document.getElementById('clear-text-btn');
const charCount = document.getElementById('char-count');
const toastContainer = document.getElementById('toast-container');

const loader = document.getElementById('loader');
const loaderTitle = document.getElementById('loader-title');
const loaderSubtext = document.getElementById('loader-subtext');
const resultsDiv = document.getElementById('results');

const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp'];

function getApiBaseUrl() {
    if (window.location.protocol === 'file:') return 'http://127.0.0.1:8000';
    return '';
}
const API_URL = getApiBaseUrl();

let activeTab = 'pdf';
let selectedFilesList = [];
let selectedKvkkFile = null;

let activeAnalysisData = null;
let activeDocumentText = '';
let currentSummaryOriginal = '';
let currentSummaryTranslated = null;
let isShowingTranslation = false;
let isShowingMasked = true;
let chatHistory = [];
let isChatSending = false;

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;

async function parseApiResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Sunucu hata bildirdi.');
        return data;
    }
    const rawText = await response.text();
    if (response.status === 502 || response.status === 503 || response.status === 504) {
        throw new Error('Sunucu uyanıyor (Render Cold Start). Lütfen 15-20 sn sonra tekrar deneyin.');
    }
    if (!response.ok) throw new Error(`Sunucu Hatası (${response.status}).`);
    throw new Error('Beklenmeyen yanıt biçimi.');
}

function showToast(message, type = 'info') {
    if (!toastContainer) return;
    toastContainer.className = 'mb-4 p-3.5 rounded-xl text-xs sm:text-sm flex items-start gap-2.5 transition-all animate-fade-in';
    let icon = 'ℹ️';
    if (type === 'error') {
        toastContainer.className += ' bg-rose-500/10 border border-rose-500/30 text-rose-300';
        icon = '⚠️';
    } else if (type === 'warning') {
        toastContainer.className += ' bg-amber-500/10 border border-amber-500/30 text-amber-300';
        icon = '⚡';
    } else if (type === 'success') {
        toastContainer.className += ' bg-emerald-500/10 border border-emerald-500/30 text-emerald-300';
        icon = '✅';
    } else {
        toastContainer.className += ' bg-blue-500/10 border border-blue-500/30 text-blue-300';
    }
    toastContainer.innerHTML = `<span class="text-base leading-none">${icon}</span><div class="flex-1 font-medium">${escapeHtml(message)}</div><button onclick="hideToast()" class="opacity-60 hover:opacity-100 ml-1 text-sm font-bold">&times;</button>`;
    toastContainer.classList.remove('hidden');
}

function hideToast() {
    if (toastContainer) toastContainer.classList.add('hidden');
}
window.hideToast = hideToast;

function scrollToSection(sectionId) {
    const el = document.getElementById(sectionId);
    if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('highlight-pulse');
        setTimeout(() => el.classList.remove('highlight-pulse'), 1600);
    }
}
window.scrollToSection = scrollToSection;

function switchTab(tabName) {
    activeTab = tabName;
    const inactiveClass = 'py-2.5 px-2 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-1.5';
    
    if (tabPdf) tabPdf.className = tabName === 'pdf' ? 'py-2.5 px-2 rounded-lg font-bold text-blue-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-1.5' : inactiveClass;
    if (tabKvkk) tabKvkk.className = tabName === 'kvkk' ? 'py-2.5 px-2 rounded-lg font-bold text-emerald-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-1.5' : inactiveClass;
    if (tabText) tabText.className = tabName === 'text' ? 'py-2.5 px-2 rounded-lg font-bold text-blue-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-2' : inactiveClass;
    if (tabCompare) tabCompare.className = tabName === 'compare' ? 'py-2.5 px-2 rounded-lg font-bold text-indigo-400 bg-slate-800/90 shadow transition-all flex items-center justify-center gap-1.5' : inactiveClass;

    if (pdfSection) pdfSection.classList.toggle('hidden', tabName !== 'pdf');
    if (kvkkSection) kvkkSection.classList.toggle('hidden', tabName !== 'kvkk');
    if (textSection) textSection.classList.toggle('hidden', tabName !== 'text');
    if (compareSection) compareSection.classList.toggle('hidden', tabName !== 'compare');
    if (resultsDiv) resultsDiv.classList.add('hidden');
    hideToast();
}

if (tabPdf) tabPdf.addEventListener('click', () => switchTab('pdf'));
if (tabKvkk) tabKvkk.addEventListener('click', () => switchTab('kvkk'));
if (tabText) tabText.addEventListener('click', () => switchTab('text'));
if (tabCompare) tabCompare.addEventListener('click', () => switchTab('compare'));

function setLoading(isLoading) {
    if (isLoading) {
        if (pdfSection) pdfSection.classList.add('hidden');
        if (kvkkSection) kvkkSection.classList.add('hidden');
        if (textSection) textSection.classList.add('hidden');
        if (compareSection) compareSection.classList.add('hidden');
        if (tabPdf && tabPdf.parentElement) tabPdf.parentElement.classList.add('hidden');
        if (resultsDiv) resultsDiv.classList.add('hidden');
        if (loader) loader.classList.remove('hidden');
    } else {
        if (loader) loader.classList.add('hidden');
        if (tabPdf && tabPdf.parentElement) tabPdf.parentElement.classList.remove('hidden');
        switchTab(activeTab);
    }
}

function resetAnalysis() {
    if (resultsDiv) { resultsDiv.classList.add('hidden'); resultsDiv.innerHTML = ''; }
    if (textInput) textInput.value = '';
    if (kvkkTextInput) kvkkTextInput.value = '';
    if (charCount) charCount.textContent = '0 karakter';
    if (kvkkCharCount) kvkkCharCount.textContent = '0 karakter';
    if (fileInput) fileInput.value = '';
    if (kvkkFileInput) kvkkFileInput.value = '';
    if (selectedFilesContainer) { selectedFilesContainer.classList.add('hidden'); selectedFilesContainer.innerHTML = ''; }
    if (kvkkSelectedFile) { kvkkSelectedFile.classList.add('hidden'); kvkkSelectedFile.innerHTML = ''; }
    selectedFilesList = [];
    selectedKvkkFile = null;
    activeAnalysisData = null;
    activeDocumentText = '';
    currentSummaryOriginal = '';
    currentSummaryTranslated = null;
    isShowingTranslation = false;
    isShowingMasked = true;
    chatHistory = [];
    isChatSending = false;
    hideToast();
    setLoading(false);
}
window.resetAnalysis = resetAnalysis;

if (textInput) {
    textInput.addEventListener('input', () => {
        if (charCount) charCount.textContent = `${textInput.value.length} karakter`;
    });
}

if (kvkkTextInput) {
    kvkkTextInput.addEventListener('input', () => {
        if (kvkkCharCount) kvkkCharCount.textContent = `${kvkkTextInput.value.length} karakter`;
    });
}

if (clearTextBtn) {
    clearTextBtn.addEventListener('click', () => {
        if (textInput) textInput.value = '';
        if (charCount) charCount.textContent = '0 karakter';
        hideToast();
    });
}

if (clearKvkkTextBtn) {
    clearKvkkTextBtn.addEventListener('click', () => {
        if (kvkkTextInput) kvkkTextInput.value = '';
        if (kvkkCharCount) kvkkCharCount.textContent = '0 karakter';
        selectedKvkkFile = null;
        if (kvkkSelectedFile) kvkkSelectedFile.classList.add('hidden');
        hideToast();
    });
}

// KVKK Tab File Selection
if (kvkkDropZone) {
    kvkkDropZone.addEventListener('click', () => { if (kvkkFileInput) kvkkFileInput.click(); });
    kvkkDropZone.addEventListener('dragover', (e) => { e.preventDefault(); kvkkDropZone.classList.add('border-emerald-500', 'bg-emerald-950/30'); });
    kvkkDropZone.addEventListener('dragleave', () => { kvkkDropZone.classList.remove('border-emerald-500', 'bg-emerald-950/30'); });
    kvkkDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        kvkkDropZone.classList.remove('border-emerald-500', 'bg-emerald-950/30');
        if (e.dataTransfer.files.length > 0) handleKvkkFileSelection(e.dataTransfer.files[0]);
    });
}

if (kvkkFileInput) {
    kvkkFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleKvkkFileSelection(e.target.files[0]);
    });
}

function handleKvkkFileSelection(file) {
    selectedKvkkFile = file;
    if (!kvkkSelectedFile) return;
    kvkkSelectedFile.innerHTML = `
        <span>📄 Seçilen Doküman: <strong>${escapeHtml(file.name)}</strong> (${(file.size / 1024).toFixed(1)} KB)</span>
        <button type="button" onclick="clearKvkkFile()" class="text-rose-400 hover:underline font-bold ml-2">✕ Kaldır</button>
    `;
    kvkkSelectedFile.classList.remove('hidden');
}

function clearKvkkFile() {
    selectedKvkkFile = null;
    if (kvkkFileInput) kvkkFileInput.value = '';
    if (kvkkSelectedFile) {
        kvkkSelectedFile.classList.add('hidden');
        kvkkSelectedFile.innerHTML = '';
    }
}
window.clearKvkkFile = clearKvkkFile;

const SAMPLES = {
    tr_cyber: "GİZLİ OLAY RAPORU: ACİL SALDIRI MÜDAHALESİ GEREKLİDİR Saat 02:00 sularında dahili izleme sistemlerimiz, merkezi kurumsal ağımızın birincil veritabanı güvenlik duvarında kritik bir arıza tespit etti.",
    tr_kvkk: "MÜŞTERİ HESAP EKSTRESİ VE GİZLİ BİLDİRİM:\nSayın Ahmet Yılmaz, 10000000146 T.C. Kimlik numaranıza ait TR12 3456 7890 1234 5678 9012 34 IBAN numaralı hesabınızdan 4543-1234-5678-9012 numaralı kredi kartınıza ödeme yapılmıştır. Detaylı bilgi için müşteri temsilciniz ile ahmet.yilmaz@kurumsal.com veya 0532 123 45 67 üzerinden iletişime geçebilirsiniz. Güvenlik bağlantı IP adresi: 192.168.1.105.",
    tr_finance: "Üçüncü Çeyrek Finansal Raporu: Şirketimiz bulut ve yapay zekâ yazılım ürünlerine olan yüksek talep sayesinde faaliyet gelirlerinde %28 oranında rekor büyüme kaydetti.",
    tr_short: "Bugün üniversitede yapay zekâ ve derin öğrenme modelleri üzerine kapsamlı bir ders işlendi.",
    en_cyber: "CONFIDENTIAL INCIDENT REPORT: IMMEDIATE ATTACK RESPONSE REQUIRED At 02:00 AM standard time, our internal monitoring systems detected a critical failure in the primary database firewall of our central corporate network.",
    en_kvkk: "EMPLOYEE CONFIDENTIAL RECORD:\nEmployee Dr. John Watson with SSN 123-45-6789 and company email john.watson@enterprise.com has been assigned internal server IP 10.0.0.45. Emergency phone contact is +1 (555) 234-5678. Corporate card: 4111-2222-3333-4444.",
    en_finance: "Quarterly Financial Overview: The company achieved a record 24% growth in operating revenue driven by strong enterprise software adoption.",
    en_short: "FastAPI is a modern, high-performance web framework for building APIs with Python."
};

function loadSample(type) {
    if (!SAMPLES[type]) return;
    if (type.includes('kvkk')) {
        if (kvkkTextInput) kvkkTextInput.value = SAMPLES[type];
        if (kvkkCharCount) kvkkCharCount.textContent = `${SAMPLES[type].length} karakter`;
        switchTab('kvkk');
    } else {
        if (textInput) textInput.value = SAMPLES[type];
        if (charCount) charCount.textContent = `${SAMPLES[type].length} karakter`;
        switchTab('text');
    }
    hideToast();
}
window.loadSample = loadSample;

async function openMetricsModal() {
    const modal = document.getElementById('metrics-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    try {
        const response = await fetch(`${API_URL}/metrics`);
        const data = await parseApiResponse(response);
        const elTotal = document.getElementById('metric-total');
        const elPii = document.getElementById('metric-pii');
        const elAvgRisk = document.getElementById('metric-avg-risk');
        if (elTotal) elTotal.textContent = data.total_processed || 0;
        if (elPii) elPii.textContent = data.total_pii_masked || 0;
        if (elAvgRisk) elAvgRisk.textContent = data.avg_risk_score || 0.0;
    } catch (err) {
        console.warn('Metrikler alınamadı:', err);
    }
}
window.openMetricsModal = openMetricsModal;

function closeMetricsModal() {
    const modal = document.getElementById('metrics-modal');
    if (modal) modal.classList.add('hidden');
}
window.closeMetricsModal = closeMetricsModal;

async function sendTestWebhook() {
    const urlInput = document.getElementById('webhook-url-input');
    const msgEl = document.getElementById('webhook-status-msg');
    if (!urlInput || !msgEl) return;
    const url = urlInput.value.trim();
    if (!url) { showToast('Lütfen bir Webhook URL girin.', 'warning'); return; }
    msgEl.classList.remove('hidden', 'text-emerald-400', 'text-rose-400');
    msgEl.textContent = 'İletiliyor...';
    try {
        const response = await fetch(`${API_URL}/webhooks/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ webhook_url: url, event_type: 'risk.critical' })
        });
        const data = await parseApiResponse(response);
        if (data.success) {
            msgEl.className = 'text-[11px] font-mono text-emerald-400 block';
            msgEl.textContent = `✅ ${data.message}`;
            showToast('Webhook testi başarıyla iletildi!', 'success');
        } else {
            msgEl.className = 'text-[11px] font-mono text-rose-400 block';
            msgEl.textContent = `❌ ${data.message}`;
        }
    } catch (err) {
        msgEl.className = 'text-[11px] font-mono text-rose-400 block';
        msgEl.textContent = `❌ Hata: ${err.message}`;
    }
}
window.sendTestWebhook = sendTestWebhook;

if (dropZone) {
    dropZone.addEventListener('click', () => { if (fileInput) fileInput.click(); });
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('border-blue-500', 'bg-slate-800/50'); });
    dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('border-blue-500', 'bg-slate-800/50'); });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-blue-500', 'bg-slate-800/50');
        if (e.dataTransfer.files.length > 0) handleFileSelection(Array.from(e.dataTransfer.files));
    });
}

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileSelection(Array.from(e.target.files));
    });
}

function handleFileSelection(files) {
    selectedFilesList = files;
    if (!selectedFilesContainer) return;
    if (files.length === 0) { selectedFilesContainer.classList.add('hidden'); return; }
    if (files.length === 1) {
        const f = files[0];
        selectedFilesContainer.innerHTML = `<div class="font-bold text-blue-400 mb-1">Seçilen Doküman (Tekil Analiz):</div><div class="flex justify-between font-mono text-xs"><span>📄 ${escapeHtml(f.name)}</span><span class="text-slate-400">${(f.size / 1024).toFixed(1)} KB</span></div>`;
    } else {
        selectedFilesContainer.innerHTML = `<div class="font-bold text-blue-400 mb-1">Seçilen Dokümanlar (${files.length} Adet - Toplu Analiz):</div><div class="space-y-1">${files.map(f => `<div class="flex justify-between font-mono text-[11px]"><span>📄 ${escapeHtml(f.name)}</span><span class="text-slate-500">${(f.size / 1024).toFixed(1)} KB</span></div>`).join('')}</div>`;
    }
    selectedFilesContainer.classList.remove('hidden');
}

if (analyzeFileBtn) {
    analyzeFileBtn.addEventListener('click', async () => {
        if (!selectedFilesList || selectedFilesList.length === 0) {
            showToast('Lütfen analiz etmek için en az 1 adet dosya seçin.', 'warning');
            return;
        }
        if (selectedFilesList.length === 1) await processSingleFile(selectedFilesList[0]);
        else await processBatchFiles(selectedFilesList);
    });
}

async function processSingleFile(file, autoScrollToMasked = false) {
    const fileName = file.name.toLowerCase();
    const isPdf = fileName.endsWith('.pdf');
    const isImage = IMAGE_EXTENSIONS.some(ext => fileName.endsWith(ext));
    if (!isPdf && !isImage && !fileName.endsWith('.txt')) {
        showToast('Lütfen geçerli bir .PDF, .TXT veya Görsel (.PNG, .JPG, .JPEG, .WEBP) dosyası seçin.', 'warning');
        return;
    }
    if (file.size > 15 * 1024 * 1024) {
        showToast('Dosya boyutu çok büyük (Maksimum 15 MB).', 'warning');
        return;
    }
    setLoading(true);
    if (isImage) {
        if (loaderTitle) loaderTitle.textContent = 'Görsel OCR ile Taranıyor';
        if (loaderSubtext) loaderSubtext.textContent = 'Yapay zekâ görüş motoru ile metinler taranıyor ve KVKK verileri maskeleniyor...';
    } else {
        if (loaderTitle) loaderTitle.textContent = 'Yapay Zekâ Analiz Ediyor';
        if (loaderSubtext) loaderSubtext.textContent = 'Doküman ayrıştırılıyor, KVKK maskelemesi ve özet çıkarılıyor...';
    }
    hideToast();
    const formData = new FormData();
    formData.append('file', file);
    const endpoint = isPdf ? `${API_URL}/analyze-pdf` : (isImage ? `${API_URL}/analyze-image` : `${API_URL}/analyze-pdf`);
    try {
        const response = await fetch(endpoint, { method: 'POST', body: formData });
        const data = await parseApiResponse(response);
        displayResults(data, autoScrollToMasked);
    } catch (error) {
        showToast(error.message, 'error');
        setLoading(false);
    }
}

async function processBatchFiles(files) {
    setLoading(true);
    if (loaderTitle) loaderTitle.textContent = 'Toplu Doküman Analizi Yapılıyor';
    if (loaderSubtext) loaderSubtext.textContent = `${files.length} adet doküman sırayla ayrıştırılıyor, özetleniyor ve birleşik risk haritası oluşturuluyor...`;
    hideToast();
    const formData = new FormData();
    for (const file of files) formData.append('files', file);
    try {
        const response = await fetch(`${API_URL}/analyze-batch`, { method: 'POST', body: formData });
        const data = await parseApiResponse(response);
        displayBatchResults(data);
    } catch (error) {
        showToast(error.message, 'error');
        setLoading(false);
    }
}

if (analyzeKvkkBtn) {
    analyzeKvkkBtn.addEventListener('click', async () => {
        if (selectedKvkkFile) {
            await processSingleFile(selectedKvkkFile, true);
            return;
        }

        const textContent = kvkkTextInput ? kvkkTextInput.value.trim() : '';
        if (!textContent) {
            showToast('Lütfen maskelenecek bir PDF/Görsel dosyası seçin veya metin girin.', 'warning');
            return;
        }
        setLoading(true);
        if (loaderTitle) loaderTitle.textContent = 'Kişisel Veriler Maskeleniyor';
        if (loaderSubtext) loaderSubtext.textContent = 'TCKN, İsim, E-posta, Telefon ve IBAN bilgileri ayıklanıp temizleniyor...';
        hideToast();
        try {
            const response = await fetch(`${API_URL}/analyze-text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textContent })
            });
            const data = await parseApiResponse(response);
            displayResults(data, true);
        } catch (error) {
            showToast(error.message, 'error');
            setLoading(false);
        }
    });
}

if (analyzeTextBtn) {
    analyzeTextBtn.addEventListener('click', async () => {
        const textContent = textInput ? textInput.value.trim() : '';
        if (!textContent) {
            showToast('Lütfen analiz edilecek bir metin girin.', 'warning');
            return;
        }
        setLoading(true);
        if (loaderTitle) loaderTitle.textContent = 'Metin Analiz Ediliyor';
        if (loaderSubtext) loaderSubtext.textContent = 'Yapay zekâ özeti, KVKK maskeleme ve risk analizi yapılıyor...';
        hideToast();
        try {
            const response = await fetch(`${API_URL}/analyze-text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textContent })
            });
            const data = await parseApiResponse(response);
            displayResults(data);
        } catch (error) {
            showToast(error.message, 'error');
            setLoading(false);
        }
    });
}

if (compareDocsBtn) {
    compareDocsBtn.addEventListener('click', async () => {
        const doc1 = compareDoc1 ? compareDoc1.value.trim() : '';
        const doc2 = compareDoc2 ? compareDoc2.value.trim() : '';
        if (!doc1 || !doc2) {
            showToast('Lütfen karşılaştırma için her iki doküman kutusuna da metin girin.', 'warning');
            return;
        }
        setLoading(true);
        if (loaderTitle) loaderTitle.textContent = 'Dokümanlar Karşılaştırılıyor';
        if (loaderSubtext) loaderSubtext.textContent = 'Semantik benzerlik, risk farkı, eklenen/çıkarılan ifadeler ve KVKK sızıntı değişimi hesaplanıyor...';
        hideToast();
        try {
            const response = await fetch(`${API_URL}/compare-documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    doc1_text: doc1,
                    doc2_text: doc2,
                    doc1_title: 'Doküman 1 (Eski)',
                    doc2_title: 'Doküman 2 (Yeni)'
                })
            });
            const data = await parseApiResponse(response);
            displayCompareResults(data);
        } catch (error) {
            showToast(error.message, 'error');
            setLoading(false);
        }
    });
}

function loadCompareSample() {
    if (compareDoc1) compareDoc1.value = 'HİZMET SÖZLEŞMESİ\nMadde 1: Taraflar arasında bulut yazılım hizmeti sağlanacaktır.\nMadde 2: Yıllık hizmet bedeli 50.000 TL olup ödemeler aylık yapılacaktır.\nMadde 3: Veri güvenliği ihlallerinde yüklenici firma 100.000 TL tazminat ödemeyi taahhüt eder.\nİletişim: destek@firmamiz.com - 0212 555 0000';
    if (compareDoc2) compareDoc2.value = 'HİZMET SÖZLEŞMESİ (REVİZE V2)\nMadde 1: Taraflar arasında bulut yazılım ve yapay zekâ altyapı hizmeti sağlanacaktır.\nMadde 2: Yıllık hizmet bedeli 85.000 TL olup ödemeler 3 aylık periyotlarla yapılacaktır.\nMadde 3: Veri ihlali durumunda yüklenici firma 500.000 TL ceza ve KVKK tazminatı üstlenir.\nMadde 4: Yetkili mahkeme İstanbul Çağlayan Mahkemeleridir.\nHassas Kayıt: TCKN 12345678901, IP: 192.168.1.50';
    showToast('Örnek karşılaştırma metinleri yüklendi.', 'success');
}
window.loadCompareSample = loadCompareSample;

async function downloadExport(format) {
    if (!activeAnalysisData) {
        showToast('İndirilecek aktif analiz verisi bulunamadı.', 'warning');
        return;
    }
    try {
        const response = await fetch(`${API_URL}/export/${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis_data: activeAnalysisData, export_format: format })
        });
        if (!response.ok) throw new Error('Rapor indirilirken sunucu hatası oluştu.');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const defaultFilename = (format === 'masked-pdf') ? 'maskelenmis_dokuman.pdf' : `doc_analysis_report.${format}`;
        a.download = defaultFilename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        const formatLabel = format === 'masked-pdf' ? 'Maskelenmiş PDF' : `.${format.toUpperCase()}`;
        showToast(`Doküman / Rapor ${formatLabel} olarak indirildi!`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}
window.downloadExport = downloadExport;


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

function toggleMaskedTextView() {
    const textDisplayEl = document.getElementById('document-text-content');
    const toggleBtn = document.getElementById('toggle-mask-btn');
    if (!textDisplayEl || !toggleBtn || !activeAnalysisData) return;
    if (isShowingMasked) {
        textDisplayEl.textContent = activeAnalysisData.cleaned_text || activeDocumentText;
        isShowingMasked = false;
        toggleBtn.innerHTML = '🔒 Maskeli Görünüme Geç';
        toggleBtn.classList.remove('bg-amber-500/20', 'border-amber-500/40', 'text-amber-300');
        toggleBtn.classList.add('bg-slate-900', 'border-slate-700', 'text-slate-300');
    } else {
        textDisplayEl.textContent = activeAnalysisData.masked_text || activeAnalysisData.cleaned_text || activeDocumentText;
        isShowingMasked = true;
        toggleBtn.innerHTML = '👁️ Orijinal Metni Gör';
        toggleBtn.classList.add('bg-amber-500/20', 'border-amber-500/40', 'text-amber-300');
        toggleBtn.classList.remove('bg-slate-900', 'border-slate-700', 'text-slate-300');
    }
}
window.toggleMaskedTextView = toggleMaskedTextView;

function copyMaskedDocument() {
    const maskedText = activeAnalysisData?.masked_text || document.getElementById('document-text-content')?.innerText || '';
    if (maskedText) {
        navigator.clipboard.writeText(maskedText).then(() => {
            const btn = document.getElementById('copy-masked-btn');
            if (btn) {
                const oldHtml = btn.innerHTML;
                btn.innerHTML = '✓ Kopyalandı';
                btn.classList.add('text-emerald-400', 'border-emerald-500/50', 'bg-emerald-500/20');
                setTimeout(() => {
                    btn.innerHTML = oldHtml;
                    btn.classList.remove('text-emerald-400', 'border-emerald-500/50', 'bg-emerald-500/20');
                }, 2000);
            }
        });
    }
}
window.copyMaskedDocument = copyMaskedDocument;

async function toggleSummaryTranslation() {
    const summaryEl = document.getElementById('summary-content');
    const translateBtn = document.getElementById('translate-btn');
    const langBadge = document.getElementById('summary-lang-indicator');
    if (!summaryEl || !translateBtn || !activeAnalysisData) return;
    const originalLang = activeAnalysisData.language || 'en';
    const targetLang = (originalLang === 'tr') ? 'en' : 'tr';
    const targetLabel = (targetLang === 'tr') ? 'Türkçe' : 'English';
    const originalLabel = (originalLang === 'tr') ? 'Türkçe' : 'English';

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

    const oldBtnContent = translateBtn.innerHTML;
    translateBtn.innerHTML = '⏳ Çevriliyor...';
    translateBtn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/translate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: currentSummaryOriginal, target_language: targetLang })
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
        showToast(`Çeviri işlemi başarısız oldu: ${err.message}`, 'warning');
        translateBtn.innerHTML = oldBtnContent;
    } finally {
        translateBtn.disabled = false;
    }
}
window.toggleSummaryTranslation = toggleSummaryTranslation;

function getRiskBadge(level, score) {
    if (level === 'High') {
        return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/15 border border-rose-500/40 text-rose-400 font-extrabold text-xs">🚨 Yüksek Risk (Skor: ${score})</span>`;
    } else if (level === 'Medium') {
        return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-400 font-extrabold text-xs">⚠️ Orta Risk (Skor: ${score})</span>`;
    }
    return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 font-extrabold text-xs">🛡️ Düşük Risk (Skor: ${score})</span>`;
}

function getMethodBadge(method, pageCount) {
    let methodText = '✍️ Metin Girişi';
    let badgeClass = 'bg-slate-800 text-slate-300 border-slate-700';
    if (method === 'vision_ocr') {
        methodText = '⚡ AI Vision OCR';
        badgeClass = 'bg-purple-500/15 text-purple-300 border-purple-500/40';
    } else if (method === 'tesseract_ocr' || method === 'ocr') {
        methodText = '🔍 OCR ile Okundu';
        badgeClass = 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40';
    } else if (method === 'digital') {
        methodText = '📄 Dijital Metin';
        badgeClass = 'bg-blue-500/15 text-blue-300 border-blue-500/40';
    }
    const pages = pageCount ? `<span class="ml-1.5 opacity-80">(${pageCount} Sayfa)</span>` : '';
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-md border text-[11px] font-semibold ${badgeClass}">${methodText}${pages}</span>`;
}

async function sendChatMessage(customQuestion = null) {
    if (isChatSending) return;
    const inputEl = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    const question = (customQuestion || inputEl?.value || '').trim();
    if (!question) return;
    if (!activeDocumentText) {
        showToast('Sohbet edebilmek için önce bir doküman analiz edilmelidir.', 'warning');
        return;
    }
    if (inputEl) inputEl.value = '';
    isChatSending = true;

    const userMsgHtml = `<div class="flex justify-end animate-fade-in"><div class="max-w-[85%] sm:max-w-[75%] p-3 rounded-2xl chat-bubble-user text-xs sm:text-sm font-medium shadow-md">${escapeHtml(question)}</div></div>`;
    messagesContainer.insertAdjacentHTML('beforeend', userMsgHtml);

    const typingId = `typing-${Date.now()}`;
    const typingHtml = `<div id="${typingId}" class="flex items-start gap-2 animate-fade-in"><div class="w-7 h-7 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs shrink-0 mt-0.5">🤖</div><div class="max-w-[85%] sm:max-w-[75%] p-3 rounded-2xl chat-bubble-ai text-xs sm:text-sm text-slate-300 shadow-md flex items-center gap-2"><span class="inline-block w-2 h-2 rounded-full bg-blue-400 animate-ping"></span><span>Doküman taranıyor ve yanıt üretiliyor...</span></div></div>`;
    messagesContainer.insertAdjacentHTML('beforeend', typingHtml);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/chat-document`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                document_text: activeDocumentText,
                question: question,
                history: chatHistory,
                language: activeAnalysisData?.language || 'tr'
            })
        });

        const data = await parseApiResponse(response);
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        const confidenceBadge = data.confidence 
            ? `<span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-semibold">🎯 %${Math.round(data.confidence * 100)} Doğruluk</span>` 
            : '';

        let sourcesHtml = '';
        if (data.sources && data.sources.length > 0) {
            const sourceItems = data.sources.map((s, idx) => `<div class="p-2 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 leading-relaxed font-mono"><span class="text-blue-400 font-bold">#${idx+1}:</span> "${escapeHtml(s.slice(0, 180))}${s.length > 180 ? '...' : ''}"</div>`).join('');
            sourcesHtml = `<details class="mt-2.5 pt-2 border-t border-slate-800/80 text-[11px]"><summary class="cursor-pointer text-slate-400 hover:text-blue-400 font-semibold select-none flex items-center gap-1"><span>📄 İlgili Kaynak Pasajları Göster (${data.sources.length})</span></summary><div class="mt-2 space-y-1.5 animate-fade-in">${sourceItems}</div></details>`;
        }

        const aiMsgHtml = `<div class="flex items-start gap-2 animate-fade-in"><div class="w-7 h-7 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs shrink-0 mt-0.5">🤖</div><div class="max-w-[85%] sm:max-w-[80%] p-3.5 rounded-2xl chat-bubble-ai text-xs sm:text-sm text-slate-100 shadow-md"><div class="flex items-center justify-between gap-2 mb-1.5"><span class="font-bold text-blue-400 text-[11px]">Doc Assistant AI</span>${confidenceBadge}</div><div class="leading-relaxed whitespace-pre-wrap">${escapeHtml(data.answer)}</div>${sourcesHtml}</div></div>`;
        messagesContainer.insertAdjacentHTML('beforeend', aiMsgHtml);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        chatHistory.push({ role: 'user', content: question });
        chatHistory.push({ role: 'assistant', content: data.answer });
    } catch (err) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        const errorMsgHtml = `<div class="flex items-start gap-2 animate-fade-in"><div class="w-7 h-7 rounded-xl bg-rose-600/20 border border-rose-500/30 flex items-center justify-center text-rose-400 text-xs shrink-0 mt-0.5">⚠️</div><div class="p-3 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs sm:text-sm">Soru yanıtlanırken bir hata oluştu: ${escapeHtml(err.message)}</div></div>`;
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

function displayResults(data, autoScrollToMasked = false) {
    loader.classList.add('hidden');
    activeAnalysisData = data;
    activeDocumentText = data.cleaned_text || '';
    currentSummaryOriginal = data.summary || '';
    currentSummaryTranslated = null;
    isShowingTranslation = false;
    isShowingMasked = true;
    chatHistory = [];
    isChatSending = false;

    const isTurkish = (data.language === 'tr');
    const riskBadge = getRiskBadge(data.risk_level, data.risk_score);
    const methodBadge = getMethodBadge(data.extraction_method, data.page_count);
    const targetLangLabel = isTurkish ? 'English' : 'Türkçe';
    const langBadge = `<span id="summary-lang-indicator" class="${isTurkish ? 'lang-badge-tr' : 'lang-badge-en'}">${data.language_label || data.language.toUpperCase()}</span>`;
    const categoryText = isTurkish 
        ? `📂 Kategori: <strong class="text-blue-400 font-bold">${escapeHtml(data.category)}</strong>`
        : `📂 Category: <strong class="text-blue-400 font-bold">${escapeHtml(data.category)}</strong>`;

    let keywordsHtml = (data.keywords || []).map(kw => `<span class="px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/25 text-blue-300 text-xs font-semibold hover:bg-blue-500/20 transition">#${escapeHtml(kw)}</span>`).join('');

    const riskReasons = data.risk_analysis?.reasons || [];
    let riskReasonsHtml = '';
    if (riskReasons.length > 0) {
        riskReasonsHtml = `<div class="mt-2.5 pt-2.5 border-t border-slate-800 text-xs"><span class="text-slate-400 font-semibold block mb-1">Tespit Edilen Güvenlik Uyarıları:</span><ul class="list-disc list-inside space-y-1 text-slate-300">${riskReasons.map(r => `<li class="text-rose-300">${escapeHtml(r)}</li>`).join('')}</ul></div>`;
    }

    const kvkk = data.kvkk_report || {};
    let piiBadgesHtml = '';
    if (data.pii_entities && data.pii_entities.length > 0) {
        piiBadgesHtml = data.pii_entities.map(p => `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium"><span class="font-bold text-rose-400">${escapeHtml(p.label)}:</span> ${escapeHtml(p.masked_value || p.text)}</span>`).join('');
    } else {
        piiBadgesHtml = '<span class="text-xs text-emerald-400 font-semibold">🛡️ Temiz — TCKN, İsim, E-posta veya Telefon sızıntısı bulunamadı.</span>';
    }

    const recs = data.action_recommendations || [];
    const anomalies = data.anomalies || [];
    const isSuspicious = data.is_suspicious || false;

    let anomalyCardHtml = '';
    if (isSuspicious || anomalies.length > 0) {
        anomalyCardHtml = `<div class="p-4 rounded-xl bg-amber-500/10 border border-amber-500/40 text-amber-200 text-xs space-y-2"><div class="flex items-center gap-2 font-bold text-amber-400 text-sm"><span>⚠️</span><span>Şüpheli İfade & Anomali Uyarısı</span></div><ul class="list-disc list-inside space-y-1 font-mono text-[11px] text-amber-300">${anomalies.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul></div>`;
    }

    let defaultQuestions = isTurkish
        ? ['Dokümanın ana konusu nedir?', 'Kritik risk veya yükümlülükler nelerdir?', 'Belgede hangi tarihler geçiyor?']
        : ['What is the main subject?', 'What are the key liabilities?', 'Which dates are mentioned?'];

    let suggestedChips = defaultQuestions.map(q => `<button type="button" onclick="askSuggestedQuestion('${escapeHtml(q)}')" class="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/25 hover:bg-indigo-500/20 text-indigo-300 text-[11px] font-medium transition">💡 ${escapeHtml(q)}</button>`).join('');

    resultsDiv.innerHTML = `
        <div class="p-4 sm:p-6 rounded-2xl glass-inner border border-blue-500/30 shadow-2xl space-y-4 animate-fade-in">
            
            <div class="flex flex-wrap items-center justify-between gap-1.5 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
                <span class="text-[11px] font-bold text-slate-400 flex items-center gap-1 pl-1">🚀 Hızlı Erişim:</span>
                <div class="flex flex-wrap gap-1">
                    <button type="button" onclick="scrollToSection('summary-section')" class="px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-300 font-semibold transition">✨ Özet</button>
                    <button type="button" onclick="scrollToSection('masked-text-section')" class="px-2.5 py-1 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 font-extrabold transition">🛡️ KVKK Maskeli Metin</button>
                    <button type="button" onclick="scrollToSection('chat-section')" class="px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 font-semibold transition">💬 Soru Sor</button>
                    <button type="button" onclick="scrollToSection('export-section')" class="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-semibold transition">📥 İndir</button>
                </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-sm sm:text-base font-bold text-slate-100">${categoryText}</span>
                    <span>•</span>
                    ${langBadge}
                </div>
                <div>${methodBadge}</div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Güvenlik Risk Düzeyi</span>
                    <div class="pt-1">${riskBadge}</div>
                    ${riskReasonsHtml}
                </div>

                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <div class="flex items-center justify-between">
                        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">KVKK / PII Uyum Durumu</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded ${kvkk.risk_level === 'Clean' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">
                            ${kvkk.risk_level || 'GÜVENLİ'}
                        </span>
                    </div>
                    <p class="text-xs font-semibold text-slate-200 pt-1">${kvkk.status || 'Hassas Veri İçermiyor'}</p>
                    <div class="flex flex-wrap gap-1.5 pt-2">${piiBadgesHtml}</div>
                </div>
            </div>

            ${anomalyCardHtml}

            <div id="summary-section" class="p-4 rounded-xl bg-slate-950/90 border border-blue-500/20 space-y-2 relative transition-all">
                <div class="flex items-center justify-between flex-wrap gap-2 border-b border-slate-800/80 pb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-blue-400 uppercase tracking-wider">✨ Akıllı Doküman Özeti</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                        <button id="translate-btn" onclick="toggleSummaryTranslation()" class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 hover:border-indigo-500 text-xs font-semibold text-slate-300 transition">🌐 ${targetLangLabel}'ye Çevir</button>
                        <button id="copy-btn" onclick="copySummary()" class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 hover:border-blue-500 text-xs font-semibold text-slate-300 transition">📋 Kopyala</button>
                    </div>
                </div>
                <p id="summary-content" class="text-xs sm:text-sm text-slate-100 leading-relaxed font-normal pt-1">${escapeHtml(data.summary)}</p>
            </div>

            <div class="space-y-1.5">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">🏷️ Öne Çıkan Anahtar Kelimeler</span>
                <div class="flex flex-wrap gap-1.5">${keywordsHtml}</div>
            </div>

            <div id="masked-text-section" class="p-4 rounded-xl bg-slate-950/90 border border-emerald-500/30 space-y-2.5 transition-all">
                <div class="flex items-center justify-between flex-wrap gap-2 border-b border-slate-800 pb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                            <span>🔒</span> İşlenmiş Doküman Metni (PII Maskeli)
                        </span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        <button id="toggle-mask-btn" onclick="toggleMaskedTextView()" class="text-xs font-semibold px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 hover:bg-amber-500/30 transition">👁️ Orijinal Metni Gör</button>
                        <button id="copy-masked-btn" onclick="copyMaskedDocument()" class="text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 hover:border-emerald-500 text-emerald-300 transition flex items-center gap-1">
                            📋 Metni Kopyala
                        </button>
                        <button id="download-masked-pdf-btn" onclick="downloadExport('masked-pdf')" class="text-xs font-bold px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow shadow-emerald-600/30 flex items-center gap-1">
                            📥 Maskelenmiş PDF İndir
                        </button>
                    </div>
                </div>
                <p class="text-[11px] text-slate-400">Metindeki tüm kişisel veriler (TCKN, İsim, E-posta, Telefon, IBAN) ayıklanıp [MASKELENDİ] etiketleriyle değiştirilmiştir. Bu metni kopyalayabilir veya doğrudan maskelenmiş PDF olarak indirebilirsiniz.</p>
                <div id="document-text-content" class="p-3 rounded-lg bg-slate-900/90 border border-slate-800/80 text-xs font-mono text-slate-200 max-h-56 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    ${escapeHtml(data.masked_text || data.cleaned_text)}
                </div>
            </div>

            ${recs.length > 0 ? `
            <div class="p-4 rounded-xl bg-slate-950/90 border border-emerald-500/20 space-y-3">
                <div class="flex items-center justify-between border-b border-slate-800 pb-2">
                    <h3 class="text-xs sm:text-sm font-bold text-emerald-400 flex items-center gap-2"><span>🎯</span> Aksiyon ve Tavsiye Listesi</h3>
                    <span class="text-[10px] text-slate-400 font-semibold">${recs.length} Öneri</span>
                </div>
                <div class="space-y-2">
                    ${recs.map((rec, idx) => {
                        let badge = 'bg-blue-500/20 text-blue-300 border-blue-500/30';
                        if (rec.priority === 'Kritik') badge = 'bg-rose-500/20 text-rose-300 border-rose-500/30';
                        else if (rec.priority === 'Yüksek') badge = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
                        return `
                            <label class="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
                                <input type="checkbox" class="mt-1 rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-emerald-500/50">
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

            <div id="chat-section" class="p-4 sm:p-5 rounded-2xl glass-inner border border-indigo-500/30 shadow-xl space-y-3.5 transition-all">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-base sm:text-lg">💬</span>
                        <div>
                            <h3 class="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                                Dokümana Soru Sor
                            </h3>
                            <p class="text-[11px] text-slate-400">Bu dokümanın içeriğine dair detayları, tarihleri veya şartları sorun.</p>
                        </div>
                    </div>
                </div>

                <div class="flex flex-wrap gap-1.5 pt-1">${suggestedChips}</div>

                <div id="chat-messages" class="max-h-[280px] overflow-y-auto chat-scroll p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-3">
                    <div class="flex items-start gap-2">
                        <div class="w-7 h-7 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-xs shrink-0 mt-0.5">🤖</div>
                        <div class="max-w-[85%] p-3 rounded-2xl chat-bubble-ai text-xs sm:text-sm text-slate-200">
                            ${isTurkish ? 'Merhaba! Bu dokümanı analiz ettim. İçerikte geçen detaylar hakkında soru sorabilirsiniz.' : 'Hello! I have analyzed this document. Feel free to ask any questions about it.'}
                        </div>
                    </div>
                </div>

                <form id="chat-form" onsubmit="event.preventDefault(); sendChatMessage();" class="flex gap-2">
                    <input type="text" id="chat-input" placeholder="${isTurkish ? 'Doküman hakkında bir soru sorun...' : 'Ask a question about this document...'}" class="flex-1 px-3.5 py-2.5 bg-slate-950/90 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition" autocomplete="off">
                    <button type="submit" id="chat-send-btn" class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-bold transition shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 shrink-0">
                        <span>Gönder</span>
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                    </button>
                </form>
            </div>

            <div id="export-section" class="p-3.5 rounded-xl glass-inner border border-emerald-500/30 flex flex-wrap items-center justify-between gap-2 shadow font-sans transition-all">
                <div class="flex items-center gap-2">
                    <span class="text-base">📥</span>
                    <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Diğer Formatlarda Rapor İndir</span>
                </div>
                <div class="flex items-center gap-1.5 flex-wrap">
                    <button type="button" onclick="downloadExport('json')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-slate-200 rounded-lg transition">JSON</button>
                    <button type="button" onclick="downloadExport('csv')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-emerald-300 rounded-lg transition">📊 CSV</button>
                    <button type="button" onclick="downloadExport('html')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-bold text-white rounded-lg transition shadow">📄 HTML Rapor</button>
                </div>
            </div>

            <button onclick="resetAnalysis()" class="w-full py-3 bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white rounded-xl font-bold text-xs sm:text-sm transition shadow-lg shadow-blue-600/30">
                ↺ Yeni Bir Doküman Analiz Et
            </button>
        </div>
    `;
    resultsDiv.classList.remove('hidden');

    if (autoScrollToMasked) {
        setTimeout(() => scrollToSection('masked-text-section'), 100);
    }
}

function displayBatchResults(data) {
    loader.classList.add('hidden');
    activeAnalysisData = data;
    const globalRiskBadge = getRiskBadge(data.global_risk_level, data.global_risk_score);
    const kvkk = data.global_kvkk_report || {};
    let docCardsHtml = '';
    (data.documents || []).forEach((docItem, idx) => {
        const a = docItem.analysis || {};
        const rBadge = getRiskBadge(a.risk_level, a.risk_score);
        docCardsHtml += `<div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2"><div class="flex items-center justify-between"><span class="font-bold text-slate-200 text-xs sm:text-sm">📄 ${idx+1}. ${escapeHtml(docItem.filename)}</span><div>${rBadge}</div></div><div class="flex items-center gap-2 text-[11px] text-slate-400"><span>📁 Kategori: <b>${escapeHtml(a.category)}</b></span><span>•</span><span>🌐 Dil: <b>${escapeHtml(a.language_label || a.language)}</b></span></div><p class="text-xs text-slate-300 leading-relaxed font-normal">${escapeHtml(a.summary)}</p></div>`;
    });
    resultsDiv.innerHTML = `
        <div class="p-4 rounded-2xl glass-inner border border-emerald-500/40 shadow-xl space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div><h2 class="text-base font-bold text-emerald-400 flex items-center gap-2">📦 Toplu Doküman Analiz Raporu</h2><p class="text-xs text-slate-400">Toplam ${data.total_documents} adet doküman işlendi ve birleşik rapor oluşturuldu.</p></div>
                <div class="flex gap-1.5">
                    <button type="button" onclick="downloadExport('json')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-slate-200 rounded-lg">JSON</button>
                    <button type="button" onclick="downloadExport('csv')" class="px-2.5 py-1 bg-slate-900 border border-slate-700 hover:border-emerald-500 text-xs font-semibold text-emerald-300 rounded-lg">📊 CSV</button>
                    <button type="button" onclick="downloadExport('html')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-bold text-white rounded-lg">📄 HTML Rapor</button>
                </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800"><span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Genel Güvenlik Riski</span><div>${globalRiskBadge}</div></div>
                <div class="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800"><span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Genel KVKK / PII Durumu</span><p class="text-xs font-bold text-emerald-300 mt-1">🛡️ ${escapeHtml(kvkk.status || 'GÜVENLİ')} (Toplam ${kvkk.total_entities || 0} Varlık)</p></div>
            </div>
            <div class="p-4 rounded-xl bg-slate-950/90 border border-emerald-500/20 space-y-1.5"><span class="text-xs font-bold text-emerald-400 uppercase tracking-wider block">✨ Genel Birleşik Özet</span><p class="text-xs sm:text-sm text-slate-100 leading-relaxed">${escapeHtml(data.overall_summary)}</p></div>
            <div class="space-y-2"><span class="text-xs font-bold text-slate-300 uppercase tracking-wider block">📂 Doküman Bazlı Analizler</span><div class="space-y-2.5">${docCardsHtml}</div></div>
        </div>
        <button onclick="resetAnalysis()" class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold text-xs sm:text-sm transition">↺ Yeni Bir Analiz Yap</button>
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
            <div class="border-b border-slate-800 pb-2"><h2 class="text-base font-bold text-indigo-400 flex items-center gap-2">⚖️ Doküman Karşılaştırma Raporu</h2><p class="text-xs text-slate-400">İki doküman arasındaki semantik benzerlik, risk değişimi ve içerik farkları aşağıdadır.</p></div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-center"><span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">İçerik Benzerliği</span><span class="text-2xl font-black ${simColor}">%${data.similarity_percentage}</span></div>
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-center"><span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Risk Skoru Değişimi</span><span class="text-xs font-bold text-slate-200 block mt-1">${data.doc1_risk_score} ➔ ${data.doc2_risk_score}</span><span class="text-[11px] font-semibold text-amber-300 block mt-0.5">${escapeHtml(data.risk_status)}</span></div>
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-center"><span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Hassas Veri (PII) Farkı</span><span class="text-lg font-bold text-indigo-300 block mt-1">${data.pii_diff_count >= 0 ? '+' : ''}${data.pii_diff_count} Varlık</span></div>
            </div>
            <div class="p-3.5 rounded-xl bg-slate-950/90 border border-indigo-500/20"><span class="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">📝 Karşılaştırma Özeti</span><p class="text-xs sm:text-sm text-slate-200 leading-relaxed">${escapeHtml(data.summary_comparison)}</p></div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div class="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-1.5"><span class="font-bold text-emerald-400 block">🟢 Eklenen Yeni İfadeler / Maddeler:</span><ul class="space-y-1 font-mono text-[11px]">${addedHtml || '<span class="text-slate-500">Yeni madde eklenmedi.</span>'}</ul></div>
                <div class="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 space-y-1.5"><span class="font-bold text-rose-400 block">🔴 Çıkarılan / Değişen İfadeler:</span><ul class="space-y-1 font-mono text-[11px]">${removedHtml || '<span class="text-slate-500">Çıkarılan madde yok.</span>'}</ul></div>
            </div>
        </div>
        <button onclick="resetAnalysis()" class="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-xs sm:text-sm transition">↺ Yeni Karşılaştırma Yap</button>
    `;
    resultsDiv.classList.remove('hidden');
}

const tabPdf = document.getElementById('tab-pdf');
const tabText = document.getElementById('tab-text');
const pdfSection = document.getElementById('pdf-section');
const textSection = document.getElementById('text-section');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const textInput = document.getElementById('text-input');
const analyzeTextBtn = document.getElementById('analyze-text-btn');

const loader = document.getElementById('loader');
const resultsDiv = document.getElementById('results');

// Otomatik API URL Tespiti (Lokal geliştirme, tek sunucu deploy veya harici frontend)
function getApiBaseUrl() {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // Doğrudan yerel dosya olarak açıldıysa
    if (protocol === 'file:') {
        return 'http://127.0.0.1:8000';
    }
    
    // Eğer sunucu üzerinden çalışıyorsa (FastAPI statik sunucu veya canlı Render/Railway deploy)
    if (window.location.origin && window.location.origin !== 'null') {
        return window.location.origin;
    }
    
    return 'https://doc-analysis-ai.onrender.com';
}

const API_URL = getApiBaseUrl();
console.log(`[API Bağlantısı] Hedef Adres: ${API_URL}`);

// Aktif Sekme Durumu (pdf | text)
let activeTab = 'pdf';

// Sekme Değiştirme Mantığı
tabPdf.addEventListener('click', () => {
    activeTab = 'pdf';
    tabPdf.classList.add('text-blue-400', 'border-blue-500');
    tabPdf.classList.remove('text-slate-500', 'border-transparent');
    tabText.classList.add('text-slate-500', 'border-transparent');
    tabText.classList.remove('text-blue-400', 'border-blue-500');
    
    pdfSection.classList.remove('hidden');
    textSection.classList.add('hidden');
    resultsDiv.classList.add('hidden');
});

tabText.addEventListener('click', () => {
    activeTab = 'text';
    tabText.classList.add('text-blue-400', 'border-blue-500');
    tabText.classList.remove('text-slate-500', 'border-transparent');
    tabPdf.classList.add('text-slate-500', 'border-transparent');
    tabPdf.classList.remove('text-blue-400', 'border-blue-500');
    
    textSection.classList.remove('hidden');
    pdfSection.classList.add('hidden');
    resultsDiv.classList.add('hidden');
});

// Dosya İşlemleri (PDF)
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

async function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showErrorMessage("Lütfen sadece geçerli bir .PDF dosyası yükleyin!");
        return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_URL}/analyze-pdf`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "PDF analizi sırasında bir hata oluştu.");
        }
        
        displayResults(data);
    } catch (error) {
        showErrorMessage(error.message);
        setLoading(false);
    }
}

// Metin Gönderme İşlemi (Text)
analyzeTextBtn.addEventListener('click', async () => {
    const textContent = textInput.value.trim();
    if (!textContent) {
        showErrorMessage("Lütfen analiz edilecek bir metin girin!");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_URL}/analyze-text`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: textContent })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Metin analizi sırasında bir hata oluştu.");
        }
        
        displayResults(data);
    } catch (error) {
        showErrorMessage(error.message);
        setLoading(false);
    }
});

// Yükleme (Loader) Durumu
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

// Hata Gösterimi
function showErrorMessage(msg) {
    alert(msg);
}

// Yeni Analiz İçin Sıfırlama Fonksiyonu (SPA Deneyimi)
function resetAnalysis() {
    resultsDiv.classList.add('hidden');
    resultsDiv.innerHTML = '';
    textInput.value = '';
    fileInput.value = '';
    
    setLoading(false);
}
window.resetAnalysis = resetAnalysis;

// Risk Seviyesi Renk ve İkon Yardımcısı
function getRiskBadge(level, score) {
    if (level === 'High') {
        return `<span class="text-rose-400 font-bold">🚨 Yüksek Risk (Skor: ${score})</span>`;
    } else if (level === 'Medium') {
        return `<span class="text-amber-400 font-bold">⚠️ Orta Risk (Skor: ${score})</span>`;
    }
    return `<span class="text-emerald-400 font-bold">🛡️ Düşük Risk (Skor: ${score})</span>`;
}

// Sonuçları Ekrana Yazdırma
function displayResults(data) {
    loader.classList.add('hidden');
    
    const riskBadge = getRiskBadge(data.risk_level, data.risk_score);
    
    resultsDiv.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
                <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Kategori</h3>
                <p class="text-xl font-bold text-slate-200 mt-1">📁 ${data.category}</p>
            </div>
            <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
                <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Güvenlik Risk Seviyesi</h3>
                <p class="text-xl mt-1">${riskBadge}</p>
            </div>
        </div>
        <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Anahtar Kelimeler & Varlıklar</h3>
            <div class="flex flex-wrap gap-2">
                ${data.keywords && data.keywords.length > 0 
                    ? data.keywords.map(kw => `<span class="px-3 py-1 bg-slate-900 border border-slate-800 text-blue-400 rounded-lg text-sm"># ${kw}</span>`).join('') 
                    : '<span class="text-slate-500 text-sm">Anahtar kelime bulunamadı.</span>'}
            </div>
        </div>
        <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Yapay Zekâ Özeti</h3>
            <p class="text-slate-300 leading-relaxed text-sm md:text-base">${data.summary}</p>
        </div>
        <button onclick="resetAnalysis()" class="w-full py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition font-medium shadow-lg shadow-blue-600/30">
            ↺ Yeni Analiz Yap
        </button>
    `;
    resultsDiv.classList.remove('hidden');
}
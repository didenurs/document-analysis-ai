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

// CANLI BACKEND URL'N BURASI (Render'dan aldığın adresle değiştir)
const API_URL = "https://document-analysis-ai.onrender.com";

// Sekme Değiştirme Mantığı
tabPdf.addEventListener('click', () => {
    tabPdf.classList.add('text-blue-400', 'border-blue-500');
    tabPdf.classList.remove('text-slate-500', 'border-transparent');
    tabText.classList.add('text-slate-500', 'border-transparent');
    tabText.classList.remove('text-blue-400', 'border-blue-500');
    
    pdfSection.classList.remove('hidden');
    textSection.classList.add('hidden');
    resultsDiv.classList.add('hidden');
});

tabText.addEventListener('click', () => {
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
    if (file.type !== "application/pdf") {
        alert("Lütfen sadece PDF dosyası yükleyin!");
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

        if (!response.ok) throw new Error("Analiz sırasında bir hata oluştu.");
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        alert(error.message);
        setLoading(false);
    }
}

// Metin Gönderme İşlemi (Text)
analyzeTextBtn.addEventListener('click', async () => {
    const textContent = textInput.value.trim();
    if (!textContent) {
        alert("Lütfen analiz edilecek bir metin girin!");
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

        if (!response.ok) throw new Error("Metin analizi sırasında bir hata oluştu.");
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        alert(error.message);
        setLoading(false);
    }
});

// Ortak Yükleme (Loader) Durumu
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
        pdfSection.classList.remove('hidden');
    }
}

// Sonuçları Ekrana Yazdırma
function displayResults(data) {
    loader.classList.add('hidden');
    
    resultsDiv.innerHTML = `
        <div class="grid grid-cols-2 gap-4">
            <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
                <h3 class="text-sm font-semibold text-slate-400 uppercase">Kategori</h3>
                <p class="text-xl font-bold text-slate-200 mt-1">${data.category}</p>
            </div>
            <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
                <h3 class="text-sm font-semibold text-slate-400 uppercase">Risk Seviyesi</h3>
                <p class="text-xl font-bold text-blue-400 mt-1">${data.risk_level} (Skor: ${data.risk_score})</p>
            </div>
        </div>
        <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
            <h3 class="text-sm font-semibold text-slate-400 uppercase mb-2">Anahtar Kelimeler</h3>
            <div class="flex flex-wrap gap-2">
                ${data.keywords.map(kw => `<span class="px-3 py-1 bg-slate-900 border border-slate-800 text-blue-400 rounded-lg text-sm">${kw}</span>`).join('')}
            </div>
        </div>
        <div class="p-4 rounded-xl border border-slate-800 bg-slate-950">
            <h3 class="text-sm font-semibold text-slate-400 uppercase mb-2">Yapay Zeka Özeti</h3>
            <p class="text-slate-300 leading-relaxed">${data.summary}</p>
        </div>
        <button onclick="location.reload()" class="w-full py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition font-medium shadow-lg shadow-blue-600/30">Yeni Analiz Yap</button>
    `;
    resultsDiv.classList.remove('hidden');
}
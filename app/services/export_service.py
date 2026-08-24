import json
import csv
import io
import pymupdf
from typing import Dict, Any

def generate_pdf_report(data: Dict[str, Any]) -> bytes:
    """
    Analiz verilerini ve maskelenmiş doküman metnini içeren,
    baskıya ve indirmeye hazır PDF raporu üretir.
    """
    doc = pymupdf.open()
    page_width, page_height = 595, 842  # A4 boyutları (72 dpi)
    margin = 40
    usable_width = page_width - (margin * 2)

    page = doc.new_page(width=page_width, height=page_height)
    y = margin

    def check_page_space(required_height: float):
        nonlocal page, y
        if y + required_height > page_height - margin:
            page = doc.new_page(width=page_width, height=page_height)
            y = margin

    # 1. BAŞLIK VE LOGO BÖLÜMÜ
    title = data.get("title_override") or ("Toplu Doküman Analiz Raporu" if "documents" in data else "Doküman Analiz & Risk Raporu")
    
    # Başlık arka plan şeridi
    page.draw_rect(pymupdf.Rect(margin, y, margin + usable_width, y + 45), color=(0.06, 0.09, 0.16), fill=(0.06, 0.09, 0.16))
    page.insert_text((margin + 12, y + 28), f"Doc Analysis AI - {title}", fontsize=15, color=(0.22, 0.74, 0.97))
    y += 55

    is_batch = "documents" in data

    if not is_batch:
        summary = data.get("summary", "")
        category = data.get("category", "Genel")
        risk_level = data.get("risk_level", "Low")
        risk_score = data.get("risk_score", 0)
        language_label = data.get("language_label", "Türkçe")
        extraction_method = data.get("extraction_method", "Metin")
        keywords = data.get("keywords", [])
        kvkk = data.get("kvkk_report", {})
        masked_text = data.get("masked_text") or data.get("cleaned_text", "")

        # 2. METRİK VAZİYET KUTUSU (Risk & KVKK)
        check_page_space(70)
        box_rect = pymupdf.Rect(margin, y, margin + usable_width, y + 65)
        page.draw_rect(box_rect, color=(0.2, 0.25, 0.33), fill=(0.95, 0.97, 1.0))
        
        info_str = (
            f"Kategori: {category}   |   Dil: {language_label}   |   Yöntem: {extraction_method}\n"
            f"Güvenlik Riski: {risk_level} (Skor: {risk_score}/100)\n"
            f"KVKK Durumu: {kvkk.get('status', 'GÜVENLİ')} (Tespit Edilen PII: {kvkk.get('total_entities', 0)} varlık)"
        )
        page.insert_textbox(pymupdf.Rect(margin + 12, y + 10, margin + usable_width - 12, y + 60), info_str, fontsize=10, color=(0.1, 0.15, 0.25))
        y += 75

        # 3. YAPAY ZEKÂ ÖZETİ
        check_page_space(80)
        page.insert_text((margin, y), "✨ Yapay Zekâ Doküman Özeti", fontsize=12, color=(0.02, 0.52, 0.78))
        y += 15
        
        summary_rect = pymupdf.Rect(margin, y, margin + usable_width, y + 120)
        written_rc = page.insert_textbox(summary_rect, summary, fontsize=9.5, color=(0.15, 0.2, 0.25))
        y += max(50, 130 - max(0, written_rc))

        # 4. ANAHTAR KELİMELER
        if keywords:
            check_page_space(35)
            kw_str = "Anahtar Kelimeler: " + ", ".join([f"#{k}" for k in keywords])
            page.insert_textbox(pymupdf.Rect(margin, y, margin + usable_width, y + 30), kw_str, fontsize=9, color=(0.3, 0.35, 0.45))
            y += 35

        # 5. MASKELEMENMİŞ DOKÜMAN METNİ
        if masked_text:
            check_page_space(100)
            page.insert_text((margin, y), "🔒 Kişisel Verileri Maskelenmiş Doküman Metni (PII Maskeli)", fontsize=11, color=(0.06, 0.6, 0.4))
            y += 18

            lines = masked_text.splitlines()
            current_chunk = []
            for line in lines:
                current_chunk.append(line)
                chunk_text = "\n".join(current_chunk)
                if len(chunk_text) > 1200:
                    check_page_space(200)
                    t_box = pymupdf.Rect(margin, y, margin + usable_width, y + (page_height - margin - y - 20))
                    page.draw_rect(t_box, color=(0.8, 0.85, 0.9), fill=(0.97, 0.98, 1.0))
                    page.insert_textbox(t_box, chunk_text, fontsize=8.5, color=(0.1, 0.1, 0.15))
                    page = doc.new_page(width=page_width, height=page_height)
                    y = margin
                    current_chunk = []

            if current_chunk:
                chunk_text = "\n".join(current_chunk)
                box_h = min(400, max(60, len(chunk_text) // 3 + 30))
                check_page_space(box_h)
                t_box = pymupdf.Rect(margin, y, margin + usable_width, y + box_h)
                page.draw_rect(t_box, color=(0.8, 0.85, 0.9), fill=(0.97, 0.98, 1.0))
                page.insert_textbox(t_box, chunk_text, fontsize=8.5, color=(0.1, 0.15, 0.2))
                y += box_h + 20

    else:
        # Toplu Rapor
        overall_summary = data.get("overall_summary", "")
        total_docs = data.get("total_documents", 0)
        global_risk = data.get("global_risk_level", "Low")
        global_score = data.get("global_risk_score", 0)

        info_str = (
            f"İşlenen Doküman Sayısı: {total_docs} adet\n"
            f"Genel Güvenlik Riski: {global_risk} (Skor: {global_score}/100)"
        )
        page.insert_textbox(pymupdf.Rect(margin, y, margin + usable_width, y + 40), info_str, fontsize=10, color=(0.1, 0.15, 0.25))
        y += 50

        page.insert_text((margin, y), "✨ Genel Birleşik Özet", fontsize=12, color=(0.02, 0.52, 0.78))
        y += 15
        written_rc = page.insert_textbox(pymupdf.Rect(margin, y, margin + usable_width, y + 150), overall_summary, fontsize=9.5, color=(0.15, 0.2, 0.25))
        y += 160

    # DİPNOT
    for p in doc:
        p.insert_text((margin, page_height - 25), "Doc Analysis AI - Otomatik Oluşturulan PDF Analiz & KVKK Raporudur.", fontsize=8, color=(0.5, 0.5, 0.5))

    return doc.tobytes()


def generate_masked_pdf_report(data: Dict[str, Any]) -> bytes:
    """
    Sadece maskelenmiş doküman metnini ve temel KVKK statüsünü içeren,
    doğrudan 3. şahıslara gönderilmeye hazır temiz maskelenmiş PDF belgesi üretir.
    """
    # data kopyası üzerinden başlığı maskeli doküman olarak ayarla
    masked_data = dict(data)
    if "documents" not in masked_data:
        masked_data["title_override"] = "Kişisel Verileri Maskelenmiş Doküman (Redacted PDF)"
    return generate_pdf_report(masked_data)


def generate_json_bytes(data: Dict[str, Any]) -> bytes:
    """Analiz verilerini yapılandırılmış JSON baytlarına dönüştürür."""
    return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')

def generate_csv_bytes(data: Dict[str, Any]) -> bytes:
    """Analiz verilerini CSV e-tablo formatına dönüştürür."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Başlık Alanları
    writer.writerow(["Alan", "Değer"])
    
    if "summary" in data:
        # Tekil Doküman Analizi
        writer.writerow(["Özet", data.get("summary", "")])
        writer.writerow(["Kategori", data.get("category", "")])
        writer.writerow(["Güvenlik Riski", f"{data.get('risk_level', '')} ({data.get('risk_score', 0)}/100)"])
        writer.writerow(["Dil", data.get("language_label", data.get("language", ""))])
        writer.writerow(["Çıkarma Yöntemi", data.get("extraction_method", "")])
        writer.writerow(["Anahtar Kelimeler", ", ".join(data.get("keywords", []))])
        
        kvkk = data.get("kvkk_report", {})
        if kvkk:
            writer.writerow(["KVKK Durumu", kvkk.get("status", "")])
            writer.writerow(["Toplam PII Varlık Sayısı", kvkk.get("total_entities", 0)])
            for entity_type, count in kvkk.get("breakdown", {}).items():
                writer.writerow([f"  - PII: {entity_type}", count])
                
    elif "documents" in data:
        # Toplu Doküman Analizi
        writer.writerow(["Toplam Doküman Sayısı", data.get("total_documents", 0)])
        writer.writerow(["Genel Birleşik Özet", data.get("overall_summary", "")])
        writer.writerow(["Genel Risk Skoru", f"{data.get('global_risk_level', '')} ({data.get('global_risk_score', 0)}/100)"])
        
        kvkk = data.get("global_kvkk_report", {})
        if kvkk:
            writer.writerow(["Genel KVKK Durumu", kvkk.get("status", "")])
            writer.writerow(["Genel PII Sayısı", kvkk.get("total_entities", 0)])
            
        writer.writerow([])
        writer.writerow(["Doküman Listesi"])
        writer.writerow(["Dosya Adı", "Kategori", "Risk Skoru", "Özet"])
        for doc in data.get("documents", []):
            analysis = doc.get("analysis", {})
            writer.writerow([
                doc.get("filename", ""),
                analysis.get("category", ""),
                f"{analysis.get('risk_level', '')} ({analysis.get('risk_score', 0)})",
                analysis.get("summary", "")
            ])

    return output.getvalue().encode('utf-8-sig')  # Excel için UTF-8 BOM ile yazılır

def generate_html_report(data: Dict[str, Any]) -> str:
    """Analiz verileri için yazdırılabilir (PDF-ready) şık bir HTML raporu oluşturur."""
    is_batch = "documents" in data
    
    title = "Toplu Doküman Analiz Raporu" if is_batch else "Doküman Analiz & Risk Raporu"
    
    if is_batch:
        summary_html = f"<div class='box'><div class='box-title'>📊 Genel Birleşik Özet</div><p>{data.get('overall_summary', '')}</p></div>"
        risk_score = data.get('global_risk_score', 0)
        risk_level = data.get('global_risk_level', 'Low')
        kvkk = data.get('global_kvkk_report', {})
        
        docs_table_rows = ""
        for doc in data.get("documents", []):
            a = doc.get("analysis", {})
            docs_table_rows += f"""
            <tr>
                <td><strong>{doc.get('filename', '')}</strong></td>
                <td>{a.get('category', '')}</td>
                <td><span class='badge risk-{a.get('risk_level', 'low').lower()}'>{a.get('risk_level', '')} ({a.get('risk_score', 0)})</span></td>
                <td>{a.get('summary', '')[:120]}...</td>
            </tr>
            """
            
        extra_content = f"""
        <div class='box'>
            <div class='box-title'>📂 Analiz Edilen Dokümanlar ({data.get('total_documents', 0)})</div>
            <table>
                <thead>
                    <tr>
                        <th>Dosya Adı</th>
                        <th>Kategori</th>
                        <th>Risk</th>
                        <th>Özet</th>
                    </tr>
                </thead>
                <tbody>
                    {docs_table_rows}
                </tbody>
            </table>
        </div>
        """
    else:
        summary_html = f"<div class='box'><div class='box-title'>✨ Yapay Zekâ Özeti</div><p>{data.get('summary', '')}</p></div>"
        risk_score = data.get('risk_score', 0)
        risk_level = data.get('risk_level', 'Low')
        kvkk = data.get('kvkk_report', {})
        
        keywords_html = "".join([f"<span class='tag'>#{kw}</span>" for kw in data.get('keywords', [])])
        
        masked_doc = data.get('masked_text') or data.get('cleaned_text', '')
        masked_box_html = f"""
        <div class='box'>
            <div class='box-title'>🔒 Kişisel Verileri Maskelenmiş Doküman Metni (KVKK / PII Redacted)</div>
            <div style='background-color: #020617; padding: 16px; border-radius: 8px; font-family: Consolas, Monaco, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-word; color: #e2e8f0; border: 1px solid #1e293b; max-height: 500px; overflow-y: auto;'>{masked_doc}</div>
        </div>
        """ if masked_doc else ""

        extra_content = f"""
        <div class='box'>
            <div class='box-title'>📁 Kategori & Metadata</div>
            <p><strong>Belge Kategorisi:</strong> {data.get('category', 'Genel')}</p>
            <p><strong>Tespit Edilen Dil:</strong> {data.get('language_label', 'Türkçe')}</p>
            <p><strong>Çıkarma Yöntemi:</strong> {data.get('extraction_method', 'Metin')}</p>
        </div>
        <div class='box'>
            <div class='box-title'>🔑 Anahtar İfadeler</div>
            <div>{keywords_html or 'Yok'}</div>
        </div>
        {masked_box_html}
        """

    risk_badge_class = f"risk-{risk_level.lower()}"
    kvkk_status = kvkk.get("status", "GÜVENLİ") if kvkk else "GÜVENLİ"
    kvkk_count = kvkk.get("total_entities", 0) if kvkk else 0

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>{title} - Doc Analysis AI</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #1e293b;
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            border: 1px solid #334155;
        }}
        .header {{
            border-bottom: 2px solid #334155;
            padding-bottom: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{
            color: #38bdf8;
            margin: 0;
            font-size: 24px;
        }}
        .badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 13px;
            display: inline-block;
        }}
        .risk-high {{ background-color: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; }}
        .risk-medium {{ background-color: #78350f; color: #fde047; border: 1px solid #eab308; }}
        .risk-low {{ background-color: #14532d; color: #86efac; border: 1px solid #22c55e; }}
        .box {{
            background-color: #0f172a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #334155;
        }}
        .box-title {{
            font-size: 14px;
            font-weight: bold;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 10px;
        }}
        .tag {{
            display: inline-block;
            background: #334155;
            color: #38bdf8;
            padding: 4px 10px;
            border-radius: 6px;
            margin-right: 6px;
            margin-bottom: 6px;
            font-size: 12px;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #334155;
            font-size: 13px;
        }}
        th {{
            color: #94a3b8;
            background-color: #1e293b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🤖 Doc Analysis AI - {title}</h1>
                <p style="color: #94a3b8; font-size: 12px; margin-top: 4px;">Oluşturulma Tarihi: Raporlama Motoru</p>
            </div>
            <div>
                <span class="badge {risk_badge_class}">Güvenlik Riski: {risk_level} ({risk_score}/100)</span>
            </div>
        </div>
        
        {summary_html}
        
        <div class="box">
            <div class="box-title">🛡️ KVKK / GDPR Uyum Durumu</div>
            <p><strong>Statü:</strong> {kvkk_status}</p>
            <p><strong>Toplam Tespit Edilen PII Varlık Sayısı:</strong> {kvkk_count}</p>
        </div>
        
        {extra_content}
        
        <div style="text-align: center; margin-top: 30px; font-size: 11px; color: #64748b;">
            Doc Analysis AI - Otomatik Oluşturulan Analiz & KVKK Raporudur.
        </div>
    </div>
</body>
</html>"""
    return html

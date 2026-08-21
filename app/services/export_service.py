import json
import csv
import io
from typing import Dict, Any

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
        .print-btn {{
            background: #10b981;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 13px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: all 0.2s;
        }}
        .print-btn:hover {{
            background: #059669;
        }}
        @media print {{
            .no-print {{ display: none !important; }}
            body {{ background-color: #fff; color: #000; padding: 0; }}
            .container {{ background-color: #fff; border: none; box-shadow: none; max-width: 100%; }}
            .box {{ background-color: #f8fafc; border: 1px solid #cbd5e1; color: #000; page-break-inside: avoid; }}
            .box-title {{ color: #475569; }}
            h1 {{ color: #0284c7; }}
            th {{ background-color: #f1f5f9; color: #334155; }}
            td {{ border-bottom: 1px solid #e2e8f0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="no-print" style="text-align: right; margin-bottom: 16px;">
            <button onclick="window.print()" class="print-btn">🖨️ PDF Olarak Kaydet / Yazdır</button>
        </div>
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

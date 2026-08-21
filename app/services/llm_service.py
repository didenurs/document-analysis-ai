import os
import httpx
from typing import Optional
from dotenv import load_dotenv

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def is_llm_available() -> bool:
    """Groq API anahtarının mevcut ve geçerli olup olmadığını kontrol eder."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    enabled = os.getenv("LLM_ENABLED", "true").lower() in ("true", "1", "yes")
    return bool(api_key and api_key != "your_groq_api_key_here" and enabled)

def generate_llm_summary(text: str, language: str = "en", model: Optional[str] = None) -> Optional[str]:
    """
    Groq LPU altyapısı (LLaMA-3.3 / LLaMA-3.1) kullanarak metni tamamen baştan,
    özgün ve akıcı bir şekilde soyutlayarak (abstractive) özetler.
    
    API anahtarı yoksa veya hata oluşursa None döner (böylece yerel fallback devreye girer).
    """
    if not is_llm_available() or not text or not text.strip():
        return None

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    selected_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    lang_name = "Türkçe" if language == "tr" else "English"
    
    system_prompt = (
        f"You are an expert, highly precise AI document summarizer. "
        f"Your task is to write a concise, professional, and completely original abstractive summary in {lang_name}. "
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. Do NOT copy sentences or tables verbatim from the input text.\n"
        f"2. Synthesize the core message, main purpose, or key takeaways in 2 to 3 concise sentences (maximum 60-80 words).\n"
        f"3. STRUCTURED DATA & TRANSCRIPTS: For transcripts, grade reports, invoices, logs, or tabular data, NEVER list raw course names, credits, or line items. Describe what the document is, who it belongs to (if applicable), and its key outcome (e.g. 'Student academic transcript showing completed engineering courses and a CGPA of 2.33.').\n"
        f"4. ALWAYS ensure the summary is completely finished and ends strictly with a full stop.\n"
        f"5. PRIVACY & PII RULE: If the input text contains masked data or privacy placeholders, keep them masked or describe them abstractly.\n"
        f"6. Output ONLY the clean summary text in {lang_name}, without meta-comments, introductory phrases (like 'Özet:' or 'Summary:'), markdown headers, or quotes."
    )

    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Text to summarize:\n\n{text}"}
        ],
        "temperature": 0.2,
        "max_tokens": 700
    }
    
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(GROQ_API_URL, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                summary = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if summary:
                    # Tırnak veya gereksiz çevreleyen karakterleri temizle
                    return summary.strip('"').strip("'").strip()
            else:
                print(f"[Groq LLM Uyarı] HTTP {response.status_code}: {response.text}")
                return None
    except Exception as e:
        print(f"[Groq LLM Bağlantı Hatası] {e}")
        return None

    return None


def translate_text(text: str, target_language: str = "tr", model: Optional[str] = None) -> Optional[str]:
    """
    Groq LLM kullanarak metni akıcı ve profesyonel bir şekilde hedef dile (TR/EN) çevirir.
    """
    if not is_llm_available() or not text or not text.strip():
        return None

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    selected_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    target_lang_name = "Türkçe" if target_language == "tr" else "English"
    
    system_prompt = (
        f"You are a professional AI translator. "
        f"Translate the following text accurately, fluently, and naturally into {target_lang_name}. "
        f"Preserve technical terms and formatting. "
        f"Output ONLY the translated text without any explanations, introductory remarks, or quotes."
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Text to translate:\n\n{text}"}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                translated = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if translated:
                    return translated.strip('"').strip("'").strip()
            else:
                print(f"[Groq Translation Uyarı] HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Groq Translation Hata] {e}")
        
    return None


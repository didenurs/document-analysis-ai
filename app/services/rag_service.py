import os
import re
import httpx
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.utils.language_detector import detect_language
from app.services.llm_service import is_llm_available, GROQ_API_URL

MULTILINGUAL_STOPWORDS = [
    # English
    "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", "this",
    "are", "was", "were", "as", "by", "an", "be", "at", "from", "or", "which", "an",
    "have", "has", "had", "will", "would", "can", "could", "should", "their", "our",
    # Turkish
    "bir", "ve", "bu", "ile", "için", "da", "de", "ise", "olan", "olarak", "gibi",
    "kadar", "daha", "çok", "en", "ancak", "veya", "tarafından", "şeklinde", "sonra",
    "önce", "üzere", "göre", "tüm", "her", "bazı", "diğer", "bunu", "bunun", "buna"
]

def chunk_document(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Doküman metnini cümle ve paragraf sınırlarına duyarlı,
    anlam bütünlüğünü koruyan örtüşmeli (overlapping) parçalara böler.
    """
    if not text or not text.strip():
        return []

    clean = text.strip()
    if len(clean) <= chunk_size:
        return [clean]

    sentences = re.split(r'(?<=[.!?\n])\s+', clean)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        
        if len(s) > chunk_size and not current_chunk:
            chunks.append(s)
            continue

        if current_length + len(s) > chunk_size and current_chunk:
            combined = " ".join(current_chunk)
            chunks.append(combined)
            words = combined.split()
            overlap_words = words[-max(2, overlap // 10):] if len(words) > 4 else []
            current_chunk = [" ".join(overlap_words), s] if overlap_words else [s]
            current_length = sum(len(x) for x in current_chunk) + len(current_chunk)
        else:
            current_chunk.append(s)
            current_length += len(s) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    return [c for c in chunks if len(c.strip()) > 15]


def retrieve_relevant_chunks(chunks: List[str], query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    TF-IDF ve Kosinüs Benzerliği kullanarak sıfır bellek tüketimiyle
    kullanıcı sorusuna en uygun Top-K pasajı tespit eder.
    """
    if not chunks or not query or not query.strip():
        return []

    try:
        lang = detect_language(query)
        stops = MULTILINGUAL_STOPWORDS if lang == "tr" else "english"

        vectorizer = TfidfVectorizer(
            token_pattern=r'(?u)\b[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]{2,}\b',
            ngram_range=(1, 2),
            stop_words=stops
        )
        
        all_corpus = chunks + [query]
        tfidf_matrix = vectorizer.fit_transform(all_corpus)
        
        chunk_vectors = tfidf_matrix[:-1]
        query_vector = tfidf_matrix[-1:]
        
        similarities = cosine_similarity(query_vector, chunk_vectors)[0]
        ranked_indices = similarities.argsort()[::-1]
        
        results = []
        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            results.append({
                "text": chunks[idx],
                "score": round(score, 3)
            })
            
        return results
    except Exception as e:
        print(f"[RAG Retrieval Uyarısı] {e}")
        return [{"text": c, "score": 0.3} for c in chunks[:top_k]]


def smart_fallback_answer(text: str, question: str, language: str = "tr") -> Dict[str, Any]:
    """
    LLM servisine erişilemediğinde veya hata alındığında, dokümandan akıllı regex
    ve kelime analizi yaparak doğrudan ve doğru yanıt üretir.
    """
    q_lower = question.lower()
    
    # 1. Tarih / Dönem Soruları
    if any(k in q_lower for k in ["tarih", "zaman", "gün", "yıl", "ay", "date", "when", "year", "dönem"]):
        date_pattern = r'\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{4}|\d{4}\s*(?:Güz|Bahar|FALL|SPRING|SUMMER))\b'
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        unique_dates = list(dict.fromkeys(dates))
        
        if unique_dates:
            lines = text.split('\n')
            matched_details = []
            for d in unique_dates:
                for line in lines:
                    if d in line and line.strip() not in matched_details:
                        matched_details.append(line.strip())
                        break
            
            if language == "tr":
                ans = "Dokümanda tespit edilen tarih, dönem ve zaman bilgileri:\n\n"
                for item in matched_details[:8]:
                    ans += f"• {item}\n"
            else:
                ans = "Dates, academic terms, and timelines found in the document:\n\n"
                for item in matched_details[:8]:
                    ans += f"• {item}\n"
            
            return {
                "answer": ans.strip(),
                "sources": matched_details[:3],
                "confidence": 0.85
            }

    # 2. Genel Cümle / Kelime Eşleştirme
    words = [w for w in re.findall(r'\w+', q_lower) if len(w) > 3 and w not in MULTILINGUAL_STOPWORDS]
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 10]
    
    matched_lines = []
    for line in lines:
        if any(w in line.lower() for w in words):
            matched_lines.append(line)

    if matched_lines:
        if language == "tr":
            ans = "Dokümanda sorunuzla ilgili tespit edilen bölümler:\n\n" + "\n".join([f"• \"{l}\"" for l in matched_lines[:4]])
        else:
            ans = "Relevant sentences found in the document:\n\n" + "\n".join([f"• \"{l}\"" for l in matched_lines[:4]])
        return {
            "answer": ans,
            "sources": matched_lines[:3],
            "confidence": 0.65
        }

    # 3. Bulunamama durumu
    no_match_text = "Doküman içeriğinde bu soruyla eşleşen spesifik bir bilgi bulunamadı." if language == "tr" else "No specific matching information found in the document."
    return {
        "answer": no_match_text,
        "sources": [text[:300]],
        "confidence": 0.30
    }


def generate_rag_answer(
    document_text: str, 
    question: str, 
    history: Optional[List[Dict[str, str]]] = None,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Doküman içeriği, kullanıcı sorusu ve geçmiş konuşmaları değerlendirerek
    Groq LLaMA motoru ile kaynak destekli, doğru yanıt üretir.
    """
    if not document_text or not document_text.strip():
        return {
            "answer": "Lütfen soru sormadan önce bir doküman yükleyin veya metin girin.",
            "sources": [],
            "confidence": 0.0,
            "language": "tr"
        }

    if not question or not question.strip():
        return {
            "answer": "Lütfen sormak istediğiniz soruyu belirtin.",
            "sources": [],
            "confidence": 0.0,
            "language": "tr"
        }

    chunks = chunk_document(document_text)
    relevant_items = retrieve_relevant_chunks(chunks, question, top_k=3)
    sources = [item["text"] for item in relevant_items if item["text"]]
    top_score = relevant_items[0]["score"] if relevant_items else 0.0
    
    detected_lang = language or detect_language(question)
    target_lang_name = "Türkçe" if detected_lang == "tr" else "English"

    # Doküman 8000 karakterden kısaysa (Transkript, Fatura vb.) TÜM dokümanı LLM'e bağlam olarak ver!
    if len(document_text) <= 8000:
        context_text = document_text
    else:
        context_text = "\n\n---\n\n".join(sources) if sources else document_text[:2000]

    # LLM varsa Groq LLaMA ile yanıtla
    if is_llm_available():
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        model = os.getenv("GROQ_MODEL", "groq/compound-mini")
        
        system_prompt = (
            f"You are a helpful, highly precise AI document assistant. "
            f"Your task is to answer the user's question accurately based ONLY on the provided document context. "
            f"CRITICAL RULES:\n"
            f"1. Answer strictly in {target_lang_name}.\n"
            f"2. Use only facts, dates, names, figures, and details directly stated in the document context.\n"
            f"3. For transcript/academic documents, list all relevant dates, course grades, GPA, or facts requested clearly in bullet points.\n"
            f"4. If the answer cannot be determined from the context, clearly say: "
            f"\"Bu bilgi sağlanan dokümanda yer almamaktadır.\" (or in English if answering in English).\n"
            f"5. Be concise, clear, and professional."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history[-4:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content and role in ("user", "assistant"):
                    messages.append({"role": role, "content": content})

        user_content = (
            f"--- DOCUMENT CONTEXT ---\n{context_text}\n--- END CONTEXT ---\n\n"
            f"Question: {question}"
        )
        messages.append({"role": "user", "content": user_content})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 600
        }

        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(GROQ_API_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if answer:
                        calculated_confidence = round(max(0.75, min(0.98, top_score + 0.4)), 2) if top_score > 0 else 0.90
                        return {
                            "answer": answer,
                            "sources": sources if sources else [document_text[:300]],
                            "confidence": calculated_confidence,
                            "language": detected_lang
                        }
                else:
                    print(f"[Groq RAG API Uyarısı] HTTP {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[Groq RAG Hatası] {e}")

    # Fallback: LLM servisi yanıt vermezse akıllı eşleme motoru
    fallback_res = smart_fallback_answer(document_text, question, detected_lang)
    return {
        "answer": fallback_res["answer"],
        "sources": fallback_res["sources"],
        "confidence": fallback_res["confidence"],
        "language": detected_lang
    }


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

def chunk_document(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    """
    Doküman metnini cümle ve paragraf sınırlarına duyarlı,
    anlam bütünlüğünü koruyan örtüşmeli (overlapping) parçalara böler.
    """
    if not text or not text.strip():
        return []

    clean = text.strip()
    if len(clean) <= chunk_size:
        return [clean]

    # Paragraflara veya cümlelere göre ayrıştır
    sentences = re.split(r'(?<=[.!?\n])\s+', clean)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        
        # Tek bir cümle chunk_size'dan büyükse doğrudan ekle
        if len(s) > chunk_size and not current_chunk:
            chunks.append(s)
            continue

        if current_length + len(s) > chunk_size and current_chunk:
            combined = " ".join(current_chunk)
            chunks.append(combined)
            
            # Örtüşme (overlap) için son birkaç kelimeyi tut
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

    if len(chunks) <= top_k:
        return [{"text": c, "score": 1.0} for c in chunks]

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
        
        # En yüksek benzerliğe göre sırala
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
        # Hata durumunda ilk pasajları dön
        return [{"text": c, "score": 0.5} for c in chunks[:top_k]]


def generate_rag_answer(
    document_text: str, 
    question: str, 
    history: Optional[List[Dict[str, str]]] = None,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Doküman içeriği, kullanıcı sorusu ve geçmiş konuşmaları değerlendirerek
    Groq LLaMA-3.3 motoru ile kaynak destekli, doğru yanıt üretir.
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

    # 1. Dokümanı parçala ve en ilgili pasajları getir
    chunks = chunk_document(document_text)
    relevant_items = retrieve_relevant_chunks(chunks, question, top_k=3)
    sources = [item["text"] for item in relevant_items if item["text"]]
    
    top_score = relevant_items[0]["score"] if relevant_items else 0.0
    detected_lang = language or detect_language(question)
    target_lang_name = "Türkçe" if detected_lang == "tr" else "English"

    # Bağlam metnini oluştur
    context_text = "\n\n---\n\n".join(sources) if sources else document_text[:1200]

    # 2. LLM varsa Groq LLaMA-3.3 ile yanıtla
    if is_llm_available():
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        model = os.getenv("GROQ_MODEL", "groq/compound-mini")
        
        system_prompt = (
            f"You are a helpful, highly precise AI document assistant. "
            f"Your task is to answer the user's question accurately based ONLY on the provided document context. "
            f"CRITICAL RULES:\n"
            f"1. Answer strictly in {target_lang_name}.\n"
            f"2. Use only facts and figures directly stated in the context.\n"
            f"3. If the answer cannot be determined from the context, clearly say: "
            f"\"Bu bilgi sağlanan dokümanda yer almamaktadır.\" (or in English if answering in English).\n"
            f"4. Be concise, clear, and professional. Structure with bullet points if helpful."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Geçmiş konuşmaları ekle (son 4 mesaj)
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
            "temperature": 0.2,
            "max_tokens": 400
        }

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(GROQ_API_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if answer:
                        return {
                            "answer": answer,
                            "sources": sources,
                            "confidence": round(max(0.65, min(0.98, top_score + 0.3)), 2),
                            "language": detected_lang
                        }
        except Exception as e:
            print(f"[Groq RAG Hatası] {e}")

    # 3. Fallback: LLM yoksa veya hata oluştuysa en ilgili pasajı öne çıkar
    if sources:
        best_passage = sources[0]
        if detected_lang == "tr":
            answer = f"Dokümandan bulunan en ilgili bölüm:\n\n\"{best_passage}\""
        else:
            answer = f"Most relevant section found in the document:\n\n\"{best_passage}\""
    else:
        answer = "Doküman içeriğinde soruyla eşleşen bir bölüm bulunamadı." if detected_lang == "tr" else "No matching section found in the document."

    return {
        "answer": answer,
        "sources": sources,
        "confidence": round(top_score, 2),
        "language": detected_lang
    }

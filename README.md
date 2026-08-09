# AI-Powered Document Analysis and Risk Assessment System

This project is a RESTful API built with **FastAPI** that leverages advanced Natural Language Processing (NLP) and Transformer models to automatically analyze text and PDF documents. The system extracts summaries, identifies key phrases, predicts document categories, and calculates potential risk levels.

---

## Features

* ** PDF & Text Processing:** Handles both raw text inputs and PDF file uploads (via `PyMuPDF`).
* ** Text Summarization:** Uses Hugging Face's `facebook/bart-large-cnn` model to generate concise summaries of long documents.
* ** Keyword Extraction:** Extracts the most relevant semantic keywords and n-grams using `KeyBERT`.
* ** Zero-Shot Classification:** Categorizes documents into predefined classes (e.g., *Cyber Security, Technology, Finance, Healthcare, Education*) using `facebook/bart-large-mnli` without requiring domain-specific training data.
* ** Risk Assessment:** A rule-based engine that scans for critical threat indicators and calculates a risk score (Low, Medium, High).
* ** Interactive API Docs:** Auto-generated Swagger UI integration for easy testing and frontend integration.

---

## Technology Stack

* **Language:** Python 3.12+
* **Backend Framework:** FastAPI, Uvicorn
* **AI / NLP Models:** HuggingFace Transformers, KeyBERT, Sentence-Transformers
* **Data Processing:** Pandas, NumPy, PyTorch
* **Document Parsing:** PyMuPDF (fitz)

---

## Project Architecture

The project follows a modular, layered architecture (Single Responsibility Principle) to ensure scalability and maintainability:

```text
document-analysis-ai/
├── app/
│   ├── api/            # API endpoints and route definitions
│   ├── services/       # Core business logic and AI model inference
│   ├── models/         # Pydantic schemas for data validation
│   └── utils/          # Helper functions (e.g., text cleaning)
├── requirements.txt    # Project dependencies
└── README.md
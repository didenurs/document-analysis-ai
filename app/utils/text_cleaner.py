import re

def clean_text(text: str) -> str:
    # Fazla boşlukları ve satır atlamalarını tek boşluğa indirger
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()
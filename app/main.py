from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="AI Document Analysis API",
    description="PDF ve metin dosyalarını analiz eden yapay zeka destekli REST API",
    version="1.0.0"
)

# Güvenlik için CORS ayarları (Frontend eklenecekse burası önemli)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpointlerimizi ana uygulamaya bağlıyoruz
app.include_router(router)
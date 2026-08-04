from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"
PRODUCT_PDF_PATH = BACKEND_DIR / "app" / "data" / "customer_support.pdf"
VECTORSTORE_PATH = BASE_DIR / "vectorestore"

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Database
    DB_URI: str

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Huggingface
    #HF_TOKEN: str
    HF_MODEL: str = "BAAI/bge-large-en-v1.5"

    # RAG
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrival type
    SEARCH_TYPE: str = "similarity"
    TOP_K: int = 8

    # Neo4j
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str


@lru_cache
def get_setting() -> Settings:
    return Settings()    

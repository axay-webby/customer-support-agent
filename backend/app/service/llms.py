from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from backend.app.core.config import get_setting


settings = get_setting()
 
def get_llm(streaming: bool = True):
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.7,
        streaming=streaming,
    ) 

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=settings.HF_MODEL
    )

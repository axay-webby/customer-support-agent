import json
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from backend.app.core.config import VECTORSTORE_PATH, get_setting
from backend.app.service.llms import get_embeddings


settings = get_setting()

STATE_FILE = VECTORSTORE_PATH / "pdf_state.json"


def _get_pdf_fingerprint(pdf_path: str | Path) -> dict[str, int | str]:
    path = Path(pdf_path)
    try:
        size_bytes = path.stat().st_size
    except FileNotFoundError:
        return {"size_bytes": 0, "chunk_count": 0}

    documents = load_document(path)
    chunks = split_documents(documents)
    return {
        "size_bytes": size_bytes,
        "chunk_count": len(chunks),
    }


def _load_state() -> dict[str, object]:
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(state: dict[str, object]) -> None:
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def should_refresh_pdf_assets(pdf_path: str | Path) -> bool:
    current = _get_pdf_fingerprint(pdf_path)
    previous = _load_state()

    if not previous:
        return True

    return previous.get("size_bytes") != current["size_bytes"] or previous.get("chunk_count") != current["chunk_count"]


# load the document
def load_document(pdf_path: str | Path):
    loader = PyPDFLoader(pdf_path)
    return loader.load()


# text splitter
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)


# vectore build
def build_vectorstore(splits):
    emb = get_embeddings()
    return FAISS.from_documents(splits, emb)


# vectorstore 
def save_vectorstore(vectorestore):
    vectorestore.save_local(str(VECTORSTORE_PATH))


# load vector store
def load_vectorstore():
    return FAISS.load_local(
        str(VECTORSTORE_PATH),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )    


# retriver
def get_retriver(vecrorstore):
    return vecrorstore.as_retriever(
        search_type = settings.SEARCH_TYPE,
        search_kwargs = {"k": settings.TOP_K},
    )


""" Full pipeline"""
def create_retriever(pdf_path: str | Path):

    should_refresh = should_refresh_pdf_assets(pdf_path)

    if should_refresh:
        documents = load_document(pdf_path)
        splits = split_documents(documents)

        vectorstore = build_vectorstore(splits)
        save_vectorstore(vectorstore)
        _save_state(_get_pdf_fingerprint(pdf_path))

    vectorstore = load_vectorstore()    
    return get_retriver(vectorstore)

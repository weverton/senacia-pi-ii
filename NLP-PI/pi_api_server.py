import os
import shutil
import logging
import tempfile
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# LangChain & AI
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer, CrossEncoder
from faster_whisper import WhisperModel

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "PORTULAN/gervasio-8b-portuguese-ptpt-decoder")
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "512"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
PDF_PATH = os.getenv("PDF_PATH", "./source/NLP/pdf/TCC  versão 4.6.pdf")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K_INITIAL = int(os.getenv("TOP_K_INITIAL", "20"))
TOP_K_FINAL = int(os.getenv("TOP_K_FINAL", "7"))
PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY", "./source/NLP/chroma_langchain_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_rag_collection")
CLEAR_DB = os.getenv("CLEAR_DB", "true").lower() == "true"
DEVICE = "cuda" if os.getenv("USE_GPU", "false").lower() == "true" else "cpu"

SYSTEM_PROMPT = """Você é um assistente útil que responde perguntas em português do Brasil (pt-BR) com base APENAS no contexto fornecido. Se a resposta não estiver no contexto, diga que não sabe. Não invente informações.

Contexto:
{context}"""

# ──────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Text question in Portuguese")

class SourceInfo(BaseModel):
    content: str
    metadata: dict

class QueryResponse(BaseModel):
    question: str
    answer: str
    status: str
    #transcribed_text: Optional[str] = None
    #sources: List[SourceInfo] = []

# ──────────────────────────────────────────────────────────────
# STT SERVICE
# ──────────────────────────────────────────────────────────────
class STTService:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info(f"✅ Whisper STT loaded on {device} ({compute_type})")

    def transcribe_file(self, audio_path: str, language: str = "pt") -> str:
        segments, _ = self.model.transcribe(audio_path, language=language, beam_size=5)
        return " ".join(seg.text for seg in segments).strip()

# ──────────────────────────────────────────────────────────────
# RAG SERVICE
# ──────────────────────────────────────────────────────────────
class CustomEmbeddings:
    def __init__(self, model_name: str, device: str):
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"✅ Embedding model loaded: {model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        prefixed = [f"passage: {t}" for t in texts]
        return self.model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([f"query: {text}"], normalize_embeddings=True).tolist()[0]

class CustomReranker:
    def __init__(self, model_name: str, top_k: int, device: str):
        self.model = CrossEncoder(model_name, device=device)
        self.top_k = top_k
        logger.info(f"✅ Reranker loaded: {model_name}")

    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        if not documents: return []
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)
        scored = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:self.top_k]]

class RAGService:
    def __init__(self):
        self.vectorstore = None
        self._load_models()

    def _load_models(self):
        self.embeddings = CustomEmbeddings(EMBEDDING_MODEL_NAME, DEVICE)
        self.reranker = CustomReranker(RERANKER_MODEL_NAME, TOP_K_FINAL, DEVICE)
        self.llm = ChatOpenAI(
            model=VLLM_MODEL, base_url=VLLM_BASE_URL, openai_api_key="EMPTY",
            temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_NEW_TOKENS, request_timeout=60.0
        )
        logger.info("✅ vLLM LLM client initialized")

    def ingest_pdf(self, pdf_path: str) -> int:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if CLEAR_DB and os.path.exists(PERSIST_DIRECTORY):
            shutil.rmtree(PERSIST_DIRECTORY)
            logger.info("Cleared Chroma DB")

        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        texts = splitter.split_documents(docs)

        for i, doc in enumerate(texts):
            doc.metadata["id"] = i
            doc.metadata["language"] = "pt-BR"

        self.vectorstore = Chroma.from_documents(
            documents=texts, embedding=self.embeddings,
            persist_directory=PERSIST_DIRECTORY, collection_name=COLLECTION_NAME
        )
        logger.info(f"✅ Ingested {len(texts)} chunks into Chroma")
        return len(texts)

    def query(self, question: str) -> dict:
        if not self.vectorstore:
            return {"status": "error", "answer": "Vector store not initialized", "sources": []}
        try:
            initial = self.vectorstore.similarity_search(question, k=TOP_K_INITIAL)
            reranked = self.reranker.rerank(question, initial)
            if not reranked:
                return {"status": "no_results", "answer": "❌ Nenhum documento relevante encontrado.", "sources": []}

            context = "\n\n".join(doc.page_content for doc in reranked)
            messages = [
                SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
                HumanMessage(content=question)
            ]
            response = self.llm.invoke(messages)
            return {
                "status": "success",
                "answer": response.content,
                "sources": [{"content": doc.page_content[:200] + "...", "metadata": doc.metadata} for doc in reranked]
            }
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {"status": "error", "answer": f"❌ Erro: {str(e)}", "sources": []}

# ──────────────────────────────────────────────────────────────
# FASTAPI APP
# ──────────────────────────────────────────────────────────────
stt_svc = None
rag_svc = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global stt_svc, rag_svc
    logger.info("🚀 Starting services...")
    stt_svc = STTService(device=DEVICE, compute_type="int8" if DEVICE == "cpu" else "float16")
    rag_svc = RAGService()
    rag_svc.ingest_pdf(PDF_PATH)
    logger.info("✅ All services loaded")
    yield
    logger.info("🛑 Shutting down...")

app = FastAPI(title="RAG + STT API", version="1.0.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": DEVICE,
        "llm": VLLM_MODEL,
        "vllm_url": VLLM_BASE_URL,
        "vectorstore": "ready" if rag_svc and rag_svc.vectorstore else "not_ready"
    }

@app.post("/query", response_model=QueryResponse)
async def query_text(req: QueryRequest):
    result = await run_in_threadpool(rag_svc.query, req.question)
    return QueryResponse(question=req.question, **result)

ALLOWED_AUDIO_MIMES = {
    "audio/mpeg", "audio/wav", "audio/x-wav", "audio/ogg", 
    "audio/opus", "audio/mp4", "audio/aac", "application/ogg"
}

@app.post("/query/audio", response_model=QueryResponse)
async def query_audio(file: UploadFile = File(...)):
    # 1️⃣ Robust MIME validation (covers audio/* + explicit OGG container type)
    mime = file.content_type or ""
    if not (mime in ALLOWED_AUDIO_MIMES or mime.startswith("audio/")):
        raise HTTPException(
            400, 
            detail="Unsupported format. Please upload MP3, WAV, OGG, OPUS, or AAC."
        )

    # 2️⃣ Enforce payload limit
    file.file.seek(0, 2)
    if file.file.tell() > 25 * 1024 * 1024:
        raise HTTPException(413, detail="Audio file exceeds 25MB limit.")
    file.file.seek(0)

    # 3️⃣ Preserve extension for ffmpeg/whisper compatibility
    ext = os.path.splitext(file.filename or "audio.ogg")[1] or ".ogg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # 4️⃣ Offload CPU-bound STT to threadpool to keep event loop responsive
        transcribed = await run_in_threadpool(stt_svc.transcribe_file, tmp_path, language="pt")
        if not transcribed.strip():
            raise HTTPException(400, detail="No speech detected or audio is unintelligible.")
        
        # 5️⃣ RAG query
        result = await run_in_threadpool(rag_svc.query, transcribed)
        return QueryResponse(question=transcribed, **result, transcribed_text=transcribed)
    finally:
        # 6️⃣ Guaranteed cleanup even on errors
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/ingest")
async def ingest_new_pdf(file: UploadFile = File(...)):
    if not file.content_type == "application/pdf":
        raise HTTPException(400, "Invalid file type. Upload a PDF.")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()
        count = await run_in_threadpool(rag_svc.ingest_pdf, tmp.name)
        return {"status": "success", "chunks_ingested": count}
    finally:
        os.unlink(tmp.name)

if __name__ == "__main__":
    uvicorn.run("pi_api_server:app", host="0.0.0.0", port=8000, reload=False)
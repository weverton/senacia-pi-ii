import streamlit as st
import requests
from requests.exceptions import RequestException, Timeout
from typing import Dict, Any

st.set_page_config(page_title="RAG+STT Assistant", page_icon="", layout="wide")

# ──────────────────────────────────────────────────────────────
# INTERNATIONALIZATION (i18n)
# ──────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt-BR"

TRANSLATIONS = {
    "pt-BR": {
        "title": "📚 Assistente de Conhecimento RAG + STT",
        "caption": "Faça perguntas por texto ou áudio. Backend: FastAPI + vLLM + Whisper + Reranker",
        "clear": "🗑️ Limpar Histórico",
        "tab_text": "💬 Pergunta por Texto",
        "tab_audio": "️ Pergunta por Áudio",
        "text_placeholder": "Ex: No que tange ao endereçamento, qual a principal diferença entre o IPv4 e o IPv6?",
        "text_submit": " Enviar Pergunta",
        "audio_info": "📁 Suporta MP3, WAV, OGG, OPUS, AAC. **Limite máximo: 25MB**.",
        "audio_upload": "Carregar arquivo de áudio",
        "audio_submit": "🎤 Transcrever & Consultar",
        "audio_size_error": "❌ Arquivo excede o limite de {limit_mb}MB permitido pelo backend.",
        "loading_text": "🔍 Buscando contexto e gerando resposta...",
        "loading_audio": "🎧 Transcrevendo áudio e consultando RAG...",
        "timeout_text": "⏱️ Tempo esgotado. O modelo pode estar carregando ou ocupado.",
        "timeout_audio": "⏱️ Tempo de transcrição esgotado. Tente um arquivo mais curto/nítido.",
        "network_error": "❌ Erro de Rede/API: {e}",
        "unexpected_error": "❌ Erro Inesperado: {e}",
        "answer_label": "💡 Resposta",
        "no_answer": "Nenhuma resposta gerada.",
        "transcribed_label": "📝 Pergunta Transcrita",
        "backend_error": "❌ Erro do Backend: {e}",
        "no_results": "⚠️ {e}",
        "lang_label": " Idioma",
        "status_online": "✅ Servidor Conectado",
        "status_offline": "⚠️ Servidor Offline"
    },
    "en-US": {
        "title": "📚 RAG + STT Knowledge Assistant",
        "caption": "Ask questions via text or audio. Backend: FastAPI + vLLM + Whisper + Reranker",
        "clear": "🗑️ Clear History",
        "tab_text": "💬 Text Query",
        "tab_audio": "🎙️ Audio Query",
        "text_placeholder": "Ex: What is the main difference between IPv4 and IPv6 addressing?",
        "text_submit": "🚀 Submit Question",
        "audio_info": "📁 Supports MP3, WAV, OGG, OPUS, AAC. **Max size: 25MB**.",
        "audio_upload": "Upload audio file",
        "audio_submit": "🎤 Transcribe & Query",
        "audio_size_error": " File exceeds the {limit_mb}MB backend limit.",
        "loading_text": "🔍 Retrieving context & generating answer...",
        "loading_audio": "🎧 Transcribing audio & querying RAG...",
        "timeout_text": "⏱️ Request timed out. The model may be loading or busy.",
        "timeout_audio": "⏱️ Transcription timeout. Try a shorter/clearer audio file.",
        "network_error": "❌ Network/API Error: {e}",
        "unexpected_error": "❌ Unexpected Error: {e}",
        "answer_label": "💡 Answer",
        "no_answer": "No answer generated.",
        "transcribed_label": " Transcribed Question",
        "backend_error": "❌ Backend Error: {e}",
        "no_results": "⚠️ {e}",
        "lang_label": "🌐 Language",
        "status_online": "✅ Server Connected",
        "status_offline": "⚠️ Server Offline"
    }
}

def t(key: str) -> str:
    lang = st.session_state.get("lang", "pt-BR")
    return TRANSLATIONS.get(lang, TRANSLATIONS["pt-BR"]).get(key, key)

# ──────────────────────────────────────────────────────────────
# API CLIENT
# ──────────────────────────────────────────────────────────────
class RAGClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    @st.cache_data(ttl=30)
    def health(_self) -> Dict[str, Any]:
        try:
            resp = _self.session.get(f"{_self.base_url}/health", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except RequestException:
            return {"status": "error", "detail": "API unreachable"}

    def query_text(self, question: str) -> Dict[str, Any]:
        resp = self.session.post(
            f"{self.base_url}/query",
            json={"question": question},
            timeout=90
        )
        resp.raise_for_status()
        return resp.json()

    def query_audio(self, file_obj) -> Dict[str, Any]:
        raw_bytes = file_obj.getvalue()
        mime = file_obj.type or "application/octet-stream"
        filename = file_obj.name or "audio.ogg"
        files = {"file": (filename, raw_bytes, mime)}
        resp = self.session.post(
            f"{self.base_url}/query/audio",
            files=files,
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()

# ──────────────────────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────────────────────
if "client" not in st.session_state:
    API_URL = st.secrets.get("API_URL", "http://pi-api:8000")
    st.session_state.client = RAGClient(API_URL)

# ──────────────────────────────────────────────────────────────
# UI HANDLERS
# ──────────────────────────────────────────────────────────────
def process_text(question: str):
    with st.spinner(t("loading_text")):
        try:
            result = st.session_state.client.query_text(question.strip())
            st.session_state.last_result = result
        except Timeout:
            st.error(t("timeout_text"))
        except RequestException as e:
            st.error(t("network_error").format(e=str(e)))
        except Exception as e:
            st.error(t("unexpected_error").format(e=str(e)))

def process_audio(file_obj):
    with st.spinner(t("loading_audio")):
        try:
            result = st.session_state.client.query_audio(file_obj)
            st.session_state.last_result = result
        except Timeout:
            st.error(t("timeout_audio"))
        except RequestException as e:
            st.error(t("network_error").format(e=str(e)))
        except Exception as e:
            st.error(t("unexpected_error").format(e=str(e)))

def display_results(result: Dict[str, Any]):
    if not result:
        return

    status = result.get("status")
    if status == "error":
        st.error(t("backend_error").format(e=result.get("answer")))
        return
    if status == "no_results":
        st.warning(t("no_results").format(e=result.get("answer")))
        return

    st.divider()
    st.subheader(t("answer_label"))
    st.write(result.get("answer", t("no_answer")))

    if result.get("transcribed_text"):
        with st.expander(t("transcribed_label"), expanded=False):
            st.info(result["transcribed_text"])

# ──────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ──────────────────────────────────────────────────────────────
def main():
    st.title(t("title"))
    st.caption(t("caption"))

    if st.button(t("clear"), use_container_width=True):
        st.session_state.pop("last_result", None)

    tab_text, tab_audio = st.tabs([t("tab_text"), t("tab_audio")])

    with tab_text:
        question = st.text_area("", height=100, placeholder=t("text_placeholder"), key="text_input")
        if st.button(t("text_submit"), type="primary", disabled=not question.strip()):
            process_text(question)

    with tab_audio:
        st.info(t("audio_info"))
        audio_file = st.file_uploader(t("audio_upload"), type=["mp3", "wav", "ogg", "opus", "m4a", "aac"], key="audio_input")
        
        if audio_file and audio_file.size > 25 * 1024 * 1024:
            st.error(t("audio_size_error").format(limit_mb=25))
            audio_file = None
            
        if st.button(t("audio_submit"), type="primary", disabled=not audio_file):
            process_audio(audio_file)

    if "last_result" in st.session_state:
        display_results(st.session_state.last_result)

    # ──────────────────────────────────────────────────────────
    # FOOTER: Fixed to bottom, Language (Left) + Friendly Status (Right)
    # ─────────────────────────────────────────────────────────
    # Spacer to prevent content overlap with fixed footer
    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)

    # CSS for fixed footer & status pill
    st.markdown(
        """
        <style>
            .footer-fixed {
                position: fixed;
                bottom: 0; left: 0; width: 100%;
                background: var(--background-color, #ffffff);
                border-top: 1px solid var(--border-color, #e0e0e0);
                padding: 12px 24px;
                z-index: 999;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 5px 12px;
                border-radius: 20px;
                background: rgba(0,0,0,0.04);
                font-size: 0.9rem;
                font-weight: 500;
                color: var(--text-color, #333333);
            }
            .status-dot {
                width: 8px; height: 8px; border-radius: 50%;
            }
            .dot-online { background: #10b981; box-shadow: 0 0 4px #10b981; }
            .dot-offline { background: #ef4444; box-shadow: 0 0 4px #ef4444; }
        </style>
        <div class="footer-fixed"></div>
        """,
        unsafe_allow_html=True
    )

    # Footer Columns
    col_lang, col_status = st.columns([1, 2])
    
    with col_lang:
        lang_idx = 0 if st.session_state.lang == "pt-BR" else 1
        st.selectbox(
            t("lang_label"),
            options=["pt-BR", "en-US"],
            index=lang_idx,
            key="footer_lang",
            label_visibility="collapsed"
        )
        st.session_state.lang = st.session_state.footer_lang

    with col_status:
        health = st.session_state.client.health()
        is_online = health.get("status") == "ok"
        status_msg = t("status_online") if is_online else t("status_offline")
        dot_class = "dot-online" if is_online else "dot-offline"
        
        st.markdown(
            f'<div class="status-pill"><span class="status-dot {dot_class}"></span> {status_msg}</div>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
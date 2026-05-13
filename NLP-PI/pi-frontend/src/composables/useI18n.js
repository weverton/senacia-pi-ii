import { ref, computed, watch } from 'vue'

const translations = {
  'pt-BR': {
    title: '📚 Assistente de Conhecimento RAG + STT',
    caption: 'Faça perguntas por texto ou áudio. Backend: FastAPI + vLLM + Whisper + Reranker',
    clear: '🗑️ Limpar Histórico',
    tabText: '💬 Pergunta por Texto',
    tabAudio: '🎙️ Pergunta por Áudio',
    tabIngest: '📚 Base de Conhecimento',
    textPlaceholder: 'Ex: No que tange ao endereçamento, qual a principal diferença entre o IPv4 e o IPv6?',
    textSubmit: '🚀 Enviar Pergunta',
    audioInfo: '📁 Suporta MP3, WAV, OGG, OPUS, AAC. Limite máximo: 25MB.',
    audioUpload: 'Carregar arquivo de áudio',
    audioSubmit: '🎤 Transcrever & Consultar',
    ingestInfo: '📄 Envie um PDF para atualizar a base de conhecimento. Limite: 25MB.',
    ingestUpload: 'Carregar arquivo PDF',
    ingestSubmit: '📤 Ingerir Documento',
    loadingText: '🔍 Buscando contexto e gerando resposta...',
    loadingAudio: ' Transcrevendo áudio e consultando RAG...',
    loadingIngest: '📚 Processando e indexando PDF...',
    errorNetwork: '❌ Erro de Rede/API',
    answerLabel: '💡 Resposta',
    noAnswer: 'Nenhuma resposta gerada.',
    transcribedLabel: '📝 Pergunta Transcrita',
    langLabel: 'Idioma',
    statusOnline: '✅ Servidor Conectado',
    statusOffline: '⚠️ Servidor Offline',
    ingestSuccess: '✅ Base atualizada! {count} blocos processados.',
    ingestError: '❌ Falha na ingestão: {e}'
  },
  'en-US': {
    title: '📚 RAG + STT Knowledge Assistant',
    caption: 'Ask questions via text or audio. Backend: FastAPI + vLLM + Whisper + Reranker',
    clear: '🗑️ Clear History',
    tabText: '💬 Text Query',
    tabAudio: '🎙️ Audio Query',
    tabIngest: '📚 Knowledge Base',
    textPlaceholder: 'Ex: What is the main difference between IPv4 and IPv6 addressing?',
    textSubmit: ' Submit Question',
    audioInfo: ' Supports MP3, WAV, OGG, OPUS, AAC. Max size: 25MB.',
    audioUpload: 'Upload audio file',
    audioSubmit: '🎤 Transcribe & Query',
    ingestInfo: '📄 Upload a PDF to update the knowledge base. Limit: 25MB.',
    ingestUpload: 'Upload PDF file',
    ingestSubmit: '📤 Ingest Document',
    loadingText: '🔍 Retrieving context & generating answer...',
    loadingAudio: ' Transcribing audio & querying RAG...',
    loadingIngest: '📚 Processing & indexing PDF...',
    errorNetwork: '❌ Network/API Error',
    answerLabel: '💡 Answer',
    noAnswer: 'No answer generated.',
    transcribedLabel: '📝 Transcribed Question',
    langLabel: 'Language',
    statusOnline: '✅ Server Connected',
    statusOffline: '️ Server Offline',
    ingestSuccess: '✅ Knowledge base updated! {count} chunks processed.',
    ingestError: '❌ Ingestion failed: {e}'
  }
}

export function useI18n() {
  const lang = ref(localStorage.getItem('app_lang') || 'pt-BR')
  const t = computed(() => translations[lang.value] || translations['pt-BR'])
  watch(lang, (newVal) => localStorage.setItem('app_lang', newVal))
  return { lang, t }
}
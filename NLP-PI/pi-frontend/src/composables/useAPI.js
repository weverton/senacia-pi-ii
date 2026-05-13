import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://pi-api:8000'
const api = axios.create({ baseURL: API_BASE, headers: { 'Accept': 'application/json' } })

export function useAPI() {
  const status = ref('checking')
  const loading = ref(false)
  const error = ref(null)
  let healthInterval = null

  const checkHealth = async () => {
    try {
      await api.get('/health', { timeout: 3000 })
      status.value = 'online'
    } catch {
      status.value = 'offline'
    }
  }

  const queryText = async (question) => {
    loading.value = true
    error.value = null
    try {
      const res = await api.post('/query', { question }, { timeout: 90000 })
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  const queryAudio = async (file) => {
    loading.value = true
    error.value = null
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/query/audio', formData, {
        timeout: 120000,
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally { loading.value = false }
  }

  // ✅ NEW: PDF Ingestion
  const ingestPDF = async (file) => {
    loading.value = true
    error.value = null
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/ingest', formData, {
        timeout: 180000, // 3min for chunking + embedding + vector store
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally { loading.value = false }
  }

  onMounted(() => { checkHealth(); healthInterval = setInterval(checkHealth, 30000) })
  onUnmounted(() => { if (healthInterval) clearInterval(healthInterval) })

  return { status, loading, error, queryText, queryAudio, ingestPDF }
}
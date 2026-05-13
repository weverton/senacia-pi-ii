<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 flex flex-col">
    <header class="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div class="max-w-4xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-800">{{ t.title }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t.caption }}</p>
      </div>
    </header>

    <main class="flex-1 px-4 py-6 sm:px-6 lg:px-8 pb-20">
      <div class="max-w-4xl mx-auto space-y-6">
        <div class="flex justify-end">
          <button @click="resetState" class="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1 px-3 py-1 rounded hover:bg-gray-100 transition">
            {{ t.clear }}
          </button>
        </div>

        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8">
            <button @click="activeTab = 'text'" :class="[activeTab === 'text' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm']">{{ t.tabText }}</button>
            <button @click="activeTab = 'audio'" :class="[activeTab === 'audio' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm']">{{ t.tabAudio }}</button>
            <button @click="activeTab = 'ingest'" :class="[activeTab === 'ingest' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm']">{{ t.tabIngest }}</button>
          </nav>
        </div>

        <!-- Text Query -->
        <div v-if="activeTab === 'text'" class="space-y-4">
          <textarea v-model="question" :placeholder="t.textPlaceholder" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y min-h-[100px] shadow-sm"></textarea>
          <button @click="handleTextSubmit" :disabled="!question.trim() || loading" class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition">
            <span v-if="loading && activeTab === 'text'" class="mr-2">⏳</span>
            {{ loading && activeTab === 'text' ? t.loadingText : t.textSubmit }}
          </button>
        </div>

        <!-- Audio Query -->
        <div v-else-if="activeTab === 'audio'" class="space-y-4">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">{{ t.audioInfo }}</div>
          <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition">
            <div class="flex flex-col items-center justify-center pt-5 pb-6">
              <svg class="w-8 h-8 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m0 0v6"></path></svg>
              <p class="mb-2 text-sm text-gray-500">{{ t.audioUpload }}</p>
              <p class="text-xs text-gray-400">{{ audioFile?.name || 'No file chosen' }}</p>
            </div>
            <input type="file" class="hidden" accept=".mp3,.wav,.ogg,.opus,.m4a,.aac" @change="handleFileSelect" />
          </label>
          <button @click="handleAudioSubmit" :disabled="!audioFile || loading" class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition">
            <span v-if="loading && activeTab === 'audio'" class="mr-2"></span>
            {{ loading && activeTab === 'audio' ? t.loadingAudio : t.audioSubmit }}
          </button>
        </div>

        <!-- PDF Ingest -->
        <div v-else-if="activeTab === 'ingest'" class="space-y-4">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">{{ t.ingestInfo }}</div>
          <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition">
            <div class="flex flex-col items-center justify-center pt-5 pb-6">
              <svg class="w-8 h-8 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              <p class="mb-2 text-sm text-gray-500">{{ t.ingestUpload }}</p>
              <p class="text-xs text-gray-400">{{ pdfFile?.name || 'No file chosen' }}</p>
            </div>
            <input type="file" class="hidden" accept=".pdf" @change="handlePdfSelect" />
          </label>
          <button @click="handleIngestSubmit" :disabled="!pdfFile || loading" class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition">
            <span v-if="loading && activeTab === 'ingest'" class="mr-2">⏳</span>
            {{ loading && activeTab === 'ingest' ? t.loadingIngest : t.ingestSubmit }}
          </button>
          <div v-if="ingestResult" class="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
            {{ t.ingestSuccess.replace('{count}', ingestResult.chunks_ingested) }}
          </div>
        </div>

        <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{{ error }}</div>

        <div v-if="result && activeTab !== 'ingest'" class="space-y-6 animate-fade-in">
          <div v-if="queryMode === 'audio' && (result.transcribed_text || result.question)" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-blue-800 mb-2">{{ t.transcribedLabel }}</h4>
            <p class="text-gray-700 text-sm whitespace-pre-wrap">{{ result.transcribed_text || result.question }}</p>
          </div>
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h3 class="text-lg font-semibold text-gray-800 mb-3">{{ t.answerLabel }}</h3>
            <div class="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">{{ result.answer || t.noAnswer }}</div>
          </div>
        </div>
      </div>
    </main>

    <footer class="fixed bottom-0 left-0 w-full bg-white border-t border-gray-200 px-4 py-3 z-50 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
      <div class="max-w-4xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500">{{ t.langLabel }}</span>
          <select v-model="lang" class="text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 py-1 px-2">
            <option value="pt-BR">🇧🇷 pt-BR</option>
            <option value="en-US">🇺🇸 en-US</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <span :class="['w-2.5 h-2.5 rounded-full', status === 'online' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]']"></span>
          <span class="text-sm font-medium text-gray-700">{{ status === 'online' ? t.statusOnline : t.statusOffline }}</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAPI } from './composables/useAPI'
import { useI18n } from './composables/useI18n'

const { status, loading, error, queryText, queryAudio, ingestPDF } = useAPI()
const { lang, t } = useI18n()

const activeTab = ref('text')
const queryMode = ref('text')
const question = ref('')
const audioFile = ref(null)
const pdfFile = ref(null)
const result = ref(null)
const ingestResult = ref(null)

const resetState = () => {
  result.value = null
  ingestResult.value = null
  error.value = null
  queryMode.value = 'text'
  question.value = ''
  audioFile.value = null
  pdfFile.value = null
}

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file && file.size > 25 * 1024 * 1024) {
    error.value = 'File exceeds 25MB limit.'
    audioFile.value = null
    return
  }
  audioFile.value = file
  error.value = null
}

const handlePdfSelect = (e) => {
  const file = e.target.files[0]
  if (file && file.size > 25 * 1024 * 1024) {
    error.value = 'PDF exceeds 25MB limit.'
    pdfFile.value = null
    return
  }
  pdfFile.value = file
  ingestResult.value = null
  error.value = null
}

const handleTextSubmit = async () => {
  if (!question.value.trim()) return
  queryMode.value = 'text'
  try { result.value = await queryText(question.value.trim()) } catch {}
}

const handleAudioSubmit = async () => {
  if (!audioFile.value) return
  queryMode.value = 'audio'
  try { result.value = await queryAudio(audioFile.value) } catch {}
}

const handleIngestSubmit = async () => {
  if (!pdfFile.value) return
  try { ingestResult.value = await ingestPDF(pdfFile.value) } catch {}
}

// Clear query results when switching away from query tabs
import { watch } from 'vue'
watch(activeTab, (newTab) => {
  if (newTab !== 'text' && newTab !== 'audio') {
    result.value = null
    queryMode.value = 'text'
  }
})
</script>

<style>
@tailwind base;
@tailwind components;
@tailwind utilities;

.animate-fade-in { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
<script setup lang="ts">
import { ref } from 'vue'
import { uploadBetsCSV } from '../services/api'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const panelOpen = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const status = ref<'idle' | 'uploading' | 'success' | 'error'>('idle')
const uploadProgress = ref(0)
const result = ref<{ filename: string; inserted: number; updated: number; skipped: number; total_bets_in_db: number } | null>(null)
const errorMessage = ref('')

function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  status.value = 'idle'
  result.value = null
  errorMessage.value = ''
}

async function ingest() {
  if (!selectedFile.value) return
  status.value = 'uploading'
  uploadProgress.value = 0
  result.value = null
  errorMessage.value = ''

  try {
    result.value = await uploadBetsCSV(selectedFile.value, (pct) => {
      uploadProgress.value = pct
    })
    status.value = 'success'

    // Refresh all app data
    await betStore.loadFilterOptions()
    await betStore.refreshAll()

    // Clear the file selection
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || err?.message || 'Upload failed'
    status.value = 'error'
  }
}

function close() {
  panelOpen.value = false
  if (status.value === 'success' || status.value === 'error') {
    status.value = 'idle'
    result.value = null
    errorMessage.value = ''
  }
}
</script>

<template>
  <div class="relative">
    <!-- Trigger button -->
    <button
      @click="panelOpen = !panelOpen"
      class="flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
      Ingest Bet Data
    </button>

    <!-- Backdrop -->
    <div v-if="panelOpen" class="fixed inset-0 z-40" @click="close" />

    <!-- Panel -->
    <div
      v-if="panelOpen"
      class="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-5 z-50"
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">Ingest Bet Data</h3>
        <button @click="close" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Select a Betfair/BetMaker CSV export file to import into the database.
        Duplicate bets will be updated automatically.
      </p>

      <!-- Hidden file input -->
      <input
        ref="fileInput"
        type="file"
        accept=".csv"
        class="hidden"
        @change="onFileSelected"
      />

      <!-- File picker area -->
      <div
        class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4 text-center cursor-pointer hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors mb-4"
        @click="openFilePicker"
      >
        <svg class="w-8 h-8 mx-auto text-gray-400 dark:text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p v-if="!selectedFile" class="text-sm text-gray-500 dark:text-gray-400">
          Click to select a <strong>.csv</strong> file
        </p>
        <p v-else class="text-sm font-medium text-indigo-600 dark:text-indigo-400 truncate">
          {{ selectedFile.name }}
          <span class="text-gray-400 font-normal ml-1">({{ (selectedFile.size / 1024).toFixed(0) }} KB)</span>
        </p>
      </div>

      <!-- Upload progress bar -->
      <div v-if="status === 'uploading'" class="mb-4">
        <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
          <span>Uploading & ingesting…</span>
          <span>{{ uploadProgress }}%</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-indigo-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: uploadProgress + '%' }"
          />
        </div>
      </div>

      <!-- Success result -->
      <div v-if="status === 'success' && result" class="mb-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
        <div class="flex items-center gap-2 text-green-700 dark:text-green-400 font-medium text-sm mb-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Ingestion complete!
        </div>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div class="bg-white dark:bg-gray-800 rounded p-2">
            <div class="text-lg font-bold text-green-600 dark:text-green-400">{{ result.inserted.toLocaleString() }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">New bets</div>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded p-2">
            <div class="text-lg font-bold text-blue-600 dark:text-blue-400">{{ result.updated.toLocaleString() }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">Updated</div>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded p-2">
            <div class="text-lg font-bold text-gray-600 dark:text-gray-400">{{ result.skipped.toLocaleString() }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">Skipped</div>
          </div>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
          {{ result.total_bets_in_db.toLocaleString() }} total bets in database
        </p>
      </div>

      <!-- Error -->
      <div v-if="status === 'error'" class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-400 flex items-start gap-2">
        <svg class="w-4 h-4 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ errorMessage }}
      </div>

      <!-- Action buttons -->
      <div class="flex gap-2">
        <button
          @click="ingest"
          :disabled="!selectedFile || status === 'uploading'"
          class="flex-1 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 dark:disabled:bg-indigo-800 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          <svg v-if="status === 'uploading'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          {{ status === 'uploading' ? 'Ingesting…' : 'Ingest' }}
        </button>
        <button
          @click="openFilePicker"
          :disabled="status === 'uploading'"
          class="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 text-gray-700 dark:text-gray-300 text-sm font-medium transition-colors"
        >
          Browse
        </button>
      </div>
    </div>
  </div>
</template>

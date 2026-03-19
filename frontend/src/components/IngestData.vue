<script setup lang="ts">
import { ref } from 'vue'
import { uploadBetsCSV, type IngestProgressEvent } from '../services/api'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const panelOpen = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const status = ref<'idle' | 'sending' | 'processing' | 'success' | 'error'>('idle')
const processedRows = ref(0)
const totalRows = ref(0)
const insertedCount = ref(0)
const updatedCount = ref(0)
const skippedCount = ref(0)
const result = ref<{ filename: string; inserted: number; updated: number; skipped: number; total_bets_in_db: number; warnings?: string[] } | null>(null)
const errorMessage = ref('')
const showHelp = ref(false)

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
  status.value = 'sending'
  processedRows.value = 0
  totalRows.value = 0
  insertedCount.value = 0
  updatedCount.value = 0
  skippedCount.value = 0
  result.value = null
  errorMessage.value = ''

  try {
    // RAF-throttled progress so even burst events look smooth
    let pendingProgress: IngestProgressEvent | null = null
    let rafHandle = 0
    const flushProgress = () => {
      rafHandle = 0
      if (pendingProgress) {
        processedRows.value = pendingProgress.processed || 0
        insertedCount.value = pendingProgress.inserted || 0
        updatedCount.value = pendingProgress.updated || 0
        skippedCount.value = pendingProgress.skipped || 0
        pendingProgress = null
      }
    }

    result.value = await uploadBetsCSV(selectedFile.value, (event: IngestProgressEvent) => {
      if (event.type === 'start') {
        totalRows.value = event.total_rows || 0
        status.value = 'processing'
      } else if (event.type === 'progress') {
        pendingProgress = event
        if (!rafHandle) {
          rafHandle = requestAnimationFrame(flushProgress)
        }
      }
    })
    // Flush any remaining progress before showing success
    if (rafHandle) cancelAnimationFrame(rafHandle)
    flushProgress()
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
  showHelp.value = false
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
      class="flex items-center gap-2 px-3 py-2 rounded-lg bg-teal-500/10 border border-teal-500/20 hover:bg-teal-500/20 text-teal-400 text-sm font-medium transition-all"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
      Ingest Data
    </button>

    <!-- Backdrop -->
    <div v-if="panelOpen" class="fixed inset-0 z-40" @click="close" />

    <!-- Panel -->
    <div
      v-if="panelOpen"
      class="absolute right-0 mt-2 w-96 glass-card !p-5 z-50 shadow-2xl shadow-black/40"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-teal-500/10 flex items-center justify-center">
            <svg class="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Ingest Bet Data</h3>
          <!-- Help icon -->
          <button
            @click.stop="showHelp = !showHelp"
            class="w-5 h-5 rounded-full bg-gray-200 dark:bg-white/10 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-white/20 hover:text-gray-700 dark:hover:text-gray-200 transition-all text-[10px] font-bold"
            title="CSV field requirements"
          >?</button>
        </div>
        <button @click="close" class="text-gray-500 hover:text-gray-300 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Help panel -->
      <div v-if="showHelp" class="mb-4 p-3 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs text-gray-600 dark:text-gray-300 space-y-2 max-h-72 overflow-y-auto">
        <p class="font-semibold text-sky-400 text-[11px] uppercase tracking-wider">CSV Field Requirements</p>

        <div>
          <p class="font-medium text-gray-800 dark:text-gray-200 mb-0.5">Required fields (import will fail without these):</p>
          <ul class="list-disc list-inside space-y-0.5 text-[11px]">
            <li><span class="font-mono text-sky-400">Profit/Loss</span> — <em>P/L</em> or <em>ProfitLoss</em></li>
            <li><span class="font-mono text-sky-400">Status</span> — <em>Status</em></li>
            <li><span class="font-mono text-sky-400">Bet ID</span> — <em>Bet Id</em> or <em>BetId</em></li>
          </ul>
        </div>

        <div>
          <p class="font-medium text-gray-800 dark:text-gray-200 mb-0.5">Recommended fields:</p>
          <ul class="list-disc list-inside space-y-0.5 text-[11px]">
            <li><span class="font-mono text-amber-400">Placed Date</span> — <em>Placed date</em> or <em>PlacedDate</em></li>
            <li><span class="font-mono text-amber-400">Strategy</span> — <em>Strategy</em> or <em>StrategyName</em></li>
            <li><span class="font-mono text-amber-400">Selection</span> — <em>Selection</em> or <em>SelectionName</em></li>
          </ul>
        </div>

        <div>
          <p class="font-medium text-gray-800 dark:text-gray-200 mb-0.5">Optional fields (used when present):</p>
          <p class="text-[11px] leading-relaxed">
            Event, Description, Bet type, Matched amount, 
            Avg. price matched, Price requested, BSP, Loss rec. amount, 
            Total matched on runner/market, Short description, Tipster, 
            Matched date, Settled date, Start time, Country code, Competition, 
            Favorite position, Market type, Market, Market ID, 
            Number of selections
          </p>
        </div>

        <div>
          <p class="font-medium text-gray-800 dark:text-gray-200 mb-0.5">BFBM optional columns (recognised &amp; ignored):</p>
          <p class="text-[10px] leading-relaxed text-gray-500">
            % of betting bank, Betting bank, Competition ID, Currency, 
            Detailed market name, Event type ID, Handicap, 
            Market type variant, Order type, P/L as % of betting bank, 
            Persistence, Price reduced, Runner position, Selection ID, 
            Settle as loss, Settle as win, Simulated bet?, 
            Size canceled, Size lapsed, Size settled, Strategy ID, 
            Strategy selection ID, Unmatched amount, Void bet
          </p>
        </div>

        <div class="pt-1 border-t border-sky-500/10 text-[10px] text-gray-500 space-y-1">
          <p>✓ Both <strong>bet_data</strong> and <strong>bet_history</strong> BFBM export formats supported</p>
          <p>✓ Column order doesn't matter</p>
          <p>✓ Files exported via Excel (CSV re-save) are supported</p>
          <p>✓ Currency symbols (£) and encoding artefacts are handled automatically</p>
        </div>
      </div>

      <p class="text-xs text-gray-500 mb-4">
        Upload a BFBM CSV export file (bet_data or bet_history format). Duplicates are handled automatically.
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
        class="border border-dashed border-gray-300 dark:border-white/10 rounded-lg p-4 text-center cursor-pointer hover:border-teal-500/40 hover:bg-teal-500/5 transition-all mb-4"
        @click="openFilePicker"
      >
        <svg class="w-8 h-8 mx-auto text-gray-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p v-if="!selectedFile" class="text-xs text-gray-500">
          Click to select a <strong class="text-gray-600 dark:text-gray-400">.csv</strong> file
        </p>
        <p v-else class="text-xs font-medium text-teal-400 truncate">
          {{ selectedFile.name }}
          <span class="text-gray-500 font-normal font-mono ml-1">({{ (selectedFile.size / 1024).toFixed(0) }} KB)</span>
        </p>
      </div>

      <!-- Sending file indicator -->
      <div v-if="status === 'sending'" class="mb-4">
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <svg class="w-3.5 h-3.5 animate-spin text-teal-400" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span>Sending file to server…</span>
        </div>
      </div>

      <!-- Processing progress -->
      <div v-if="status === 'processing'" class="mb-4">
        <div class="flex justify-between text-[10px] text-gray-500 uppercase tracking-wider mb-1">
          <span>Processing bets…</span>
          <span class="font-mono text-teal-400">{{ processedRows.toLocaleString() }} / {{ totalRows.toLocaleString() }}</span>
        </div>
        <div class="w-full bg-gray-100 dark:bg-white/5 rounded-full h-1.5 overflow-hidden">
          <div
            class="bg-gradient-to-r from-teal-500 to-emerald-400 h-1.5 rounded-full transition-all duration-300"
            :style="{ width: (totalRows > 0 ? Math.min(100, processedRows / totalRows * 100) : 0) + '%' }"
          />
        </div>
        <div class="flex gap-3 mt-2 text-[10px] font-mono">
          <span class="text-emerald-400">{{ insertedCount.toLocaleString() }} new</span>
          <span class="text-sky-400">{{ updatedCount.toLocaleString() }} updated</span>
          <span class="text-gray-400">{{ skippedCount.toLocaleString() }} skipped</span>
        </div>
      </div>

      <!-- Success result -->
      <div v-if="status === 'success' && result" class="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
        <div class="flex items-center gap-2 text-emerald-400 font-medium text-xs mb-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Ingestion complete!
        </div>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div class="bg-gray-100 dark:bg-white/5 rounded-lg p-2">
            <div class="text-base font-bold font-mono text-emerald-400">{{ result.inserted.toLocaleString() }}</div>
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">New</div>
          </div>
          <div class="bg-gray-100 dark:bg-white/5 rounded-lg p-2">
            <div class="text-base font-bold font-mono text-sky-400">{{ result.updated.toLocaleString() }}</div>
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Updated</div>
          </div>
          <div class="bg-gray-100 dark:bg-white/5 rounded-lg p-2">
            <div class="text-base font-bold font-mono text-gray-400">{{ result.skipped.toLocaleString() }}</div>
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Skipped</div>
          </div>
        </div>
        <p class="text-[10px] text-gray-500 mt-2 text-center font-mono">
          {{ result.total_bets_in_db.toLocaleString() }} total bets in database
        </p>
        <!-- Ingestion warnings -->
        <div v-if="result.warnings && result.warnings.length" class="mt-2 pt-2 border-t border-emerald-500/10">
          <p class="text-[10px] text-amber-400 font-medium mb-1">⚠ Warnings:</p>
          <ul class="space-y-0.5">
            <li v-for="(w, i) in result.warnings" :key="i" class="text-[10px] text-amber-400/80 leading-tight">
              {{ w }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Error -->
      <div v-if="status === 'error'" class="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-start gap-2">
        <svg class="w-4 h-4 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ errorMessage }}
      </div>

      <!-- Action buttons -->
      <div class="flex gap-2">
        <button
          @click="ingest"
          :disabled="!selectedFile || status === 'sending' || status === 'processing'"
          class="btn-glow flex-1 !py-2 !text-xs flex items-center justify-center gap-2"
          :class="{ 'opacity-40 cursor-not-allowed': !selectedFile || status === 'sending' || status === 'processing' }"
        >
          <svg v-if="status === 'sending' || status === 'processing'" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          {{ status === 'sending' ? 'Sending…' : status === 'processing' ? 'Processing…' : 'Ingest' }}
        </button>
        <button
          @click="openFilePicker"
          :disabled="status === 'sending' || status === 'processing'"
          class="px-4 py-2 rounded-lg bg-gray-100 dark:bg-white/5 border border-gray-300 dark:border-white/10 hover:bg-gray-200 dark:hover:bg-white/10 disabled:opacity-30 text-gray-600 dark:text-gray-300 text-xs font-medium transition-all"
        >
          Browse
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBetStore } from '../stores/betStore'
import ConfirmDialog from './ConfirmDialog.vue'

const betStore = useBetStore()

// ─── Tab state ───────────────────────────────────────────────────────────────
const activeSubTab = ref<'suggestions' | 'manual'>('suggestions')

// ─── Merge Suggestions state ─────────────────────────────────────────────────
const suggestionsLoading = ref(false)
const expandedSuggestion = ref<string | null>(null)
const suggestionTargets = ref<Record<string, string>>({})
const showSuggestionConfirm = ref(false)
const pendingSuggestionMerge = ref<{ strategyId: string; sources: string[]; target: string } | null>(null)
const mergeResult = ref<{ message: string; type: 'success' | 'error' } | null>(null)

// ─── Manual Merge state ──────────────────────────────────────────────────────
const manualSearchQuery = ref('')
const selectedForMerge = ref<Set<string>>(new Set())
const manualTargetName = ref('')
const showManualConfirm = ref(false)
const manualLoading = ref(false)

onMounted(async () => {
  suggestionsLoading.value = true
  await Promise.all([
    betStore.loadMergeSuggestions(),
    betStore.loadAllStrategies(),
  ])
  suggestionsLoading.value = false
})

// ─── Suggestions helpers ─────────────────────────────────────────────────────
function toggleSuggestion(strategyId: string) {
  if (expandedSuggestion.value === strategyId) {
    expandedSuggestion.value = null
  } else {
    expandedSuggestion.value = strategyId
    // Default target to the strategy with the most bets
    const suggestion = betStore.mergeSuggestions.find(s => s.strategy_id === strategyId)
    if (suggestion && suggestion.strategies.length > 0 && !suggestionTargets.value[strategyId]) {
      const first = suggestion.strategies[0]
      if (first) {
        suggestionTargets.value[strategyId] = first.strategy
      }
    }
  }
}

function startSuggestionMerge(strategyId: string) {
  const suggestion = betStore.mergeSuggestions.find(s => s.strategy_id === strategyId)
  if (!suggestion) return
  const target = suggestionTargets.value[strategyId]
  if (!target) return
  const sources = suggestion.strategies.map(s => s.strategy).filter(s => s !== target)
  pendingSuggestionMerge.value = { strategyId, sources, target }
  showSuggestionConfirm.value = true
}

async function confirmSuggestionMerge() {
  if (!pendingSuggestionMerge.value) return
  const { sources, target } = pendingSuggestionMerge.value
  try {
    const result = await betStore.mergeStrategies(sources, target)
    mergeResult.value = {
      message: `Merged ${result.merged_bets} bets into "${target}"`,
      type: 'success',
    }
    expandedSuggestion.value = null
  } catch {
    mergeResult.value = { message: 'Merge failed. Please try again.', type: 'error' }
  }
  showSuggestionConfirm.value = false
  pendingSuggestionMerge.value = null
  setTimeout(() => { mergeResult.value = null }, 4000)
}

// ─── Manual merge helpers ────────────────────────────────────────────────────
const filteredStrategies = computed(() => {
  if (!manualSearchQuery.value) return betStore.allStrategies
  const q = manualSearchQuery.value.toLowerCase()
  return betStore.allStrategies.filter(s => s.strategy.toLowerCase().includes(q))
})

function toggleManualSelect(strategy: string) {
  const newSet = new Set(selectedForMerge.value)
  if (newSet.has(strategy)) {
    newSet.delete(strategy)
  } else {
    newSet.add(strategy)
  }
  selectedForMerge.value = newSet
  // Auto-set target to the first selected strategy if empty
  if (!manualTargetName.value && newSet.size > 0) {
    manualTargetName.value = strategy
  }
}

function selectAllVisible() {
  if (selectedForMerge.value.size === filteredStrategies.value.length) {
    selectedForMerge.value = new Set()
  } else {
    selectedForMerge.value = new Set(filteredStrategies.value.map(s => s.strategy))
  }
}

const selectedStrategiesList = computed(() => {
  return betStore.allStrategies.filter(s => selectedForMerge.value.has(s.strategy))
})

const canMerge = computed(() => {
  return selectedForMerge.value.size >= 2 && manualTargetName.value.trim().length > 0
})

function startManualMerge() {
  if (!canMerge.value) return
  showManualConfirm.value = true
}

async function confirmManualMerge() {
  const target = manualTargetName.value.trim()
  const sources = Array.from(selectedForMerge.value).filter(s => s !== target)
  if (!sources.length) {
    mergeResult.value = { message: 'All selected strategies already have the target name.', type: 'error' }
    showManualConfirm.value = false
    return
  }
  manualLoading.value = true
  try {
    const result = await betStore.mergeStrategies(sources, target)
    mergeResult.value = {
      message: `Merged ${result.merged_bets} bets from ${sources.length} strategies into "${target}"`,
      type: 'success',
    }
    selectedForMerge.value = new Set()
    manualTargetName.value = ''
  } catch {
    mergeResult.value = { message: 'Merge failed. Please try again.', type: 'error' }
  }
  showManualConfirm.value = false
  manualLoading.value = false
  setTimeout(() => { mergeResult.value = null }, 4000)
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatPL(value: number) {
  const formatted = Math.abs(value).toFixed(2)
  return value >= 0 ? `+£${formatted}` : `-£${formatted}`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">Strategy Manager</h2>
      <p class="mt-1 text-sm text-gray-500">
        Merge strategies that share the same BFBM StrategyID, or manually combine strategy names.
      </p>
    </div>

    <!-- Result toast -->
    <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-2">
      <div v-if="mergeResult" class="p-3 rounded-lg text-sm font-medium" :class="mergeResult.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'">
        {{ mergeResult.message }}
      </div>
    </Transition>

    <!-- Sub-tabs -->
    <div class="pill-nav">
      <button @click="activeSubTab = 'suggestions'" :class="activeSubTab === 'suggestions' ? 'active' : ''">
        <span class="flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
          Auto-Suggestions
          <span v-if="betStore.mergeSuggestions.length > 0" class="ml-1 inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none rounded-full bg-amber-500/20 text-amber-400">{{ betStore.mergeSuggestions.length }}</span>
        </span>
      </button>
      <button @click="activeSubTab = 'manual'" :class="activeSubTab === 'manual' ? 'active' : ''">
        <span class="flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          Manual Merge
        </span>
      </button>
    </div>

    <!-- ═══════ Auto-Suggestions Tab ═══════ -->
    <div v-if="activeSubTab === 'suggestions'">
      <div v-if="suggestionsLoading" class="glass-card p-8 text-center">
        <div class="animate-spin inline-block w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full"></div>
        <p class="mt-3 text-sm text-gray-500">Scanning for strategies with matching IDs…</p>
      </div>

      <div v-else-if="betStore.mergeSuggestions.length === 0" class="glass-card p-8 text-center">
        <svg class="mx-auto w-12 h-12 text-gray-300 dark:text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <h3 class="mt-3 text-sm font-semibold text-gray-700 dark:text-gray-300">No merge suggestions</h3>
        <p class="mt-1 text-xs text-gray-500">
          No strategies with matching StrategyIDs were found. This either means your CSV exports don't include the StrategyID column, or all strategies already have consistent names.
        </p>
        <p class="mt-3 text-xs text-gray-400">
          <strong>Tip:</strong> In BFBM, right-click any column header → "Column chooser" → enable "StrategyID" before exporting.
        </p>
      </div>

      <div v-else class="space-y-3">
        <p class="text-xs text-gray-500">
          These strategies share the same BFBM StrategyID, which may indicate they are the same strategy renamed over time.
          <strong>Note:</strong> Same IDs don't guarantee the same strategy — different BFBM installations can reuse IDs.
        </p>

        <div v-for="suggestion in betStore.mergeSuggestions" :key="suggestion.strategy_id" class="glass-card overflow-hidden">
          <!-- Suggestion header -->
          <button @click="toggleSuggestion(suggestion.strategy_id)" class="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
            <div class="flex items-center gap-3 min-w-0">
              <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
              </div>
              <div class="text-left min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  StrategyID: {{ suggestion.strategy_id }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ suggestion.strategies.length }} strategy names · {{ suggestion.strategies.reduce((s, m) => s + m.num_bets, 0) }} total bets
                </p>
              </div>
            </div>
            <svg class="w-5 h-5 text-gray-400 transition-transform" :class="{ 'rotate-180': expandedSuggestion === suggestion.strategy_id }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>

          <!-- Expanded detail -->
          <Transition enter-active-class="transition-all duration-200 ease-out" enter-from-class="max-h-0 opacity-0" enter-to-class="max-h-[600px] opacity-100" leave-active-class="transition-all duration-150 ease-in" leave-from-class="max-h-[600px] opacity-100" leave-to-class="max-h-0 opacity-0">
            <div v-if="expandedSuggestion === suggestion.strategy_id" class="border-t border-gray-100 dark:border-gray-800/40 overflow-hidden">
              <div class="px-4 py-3 space-y-3">
                <!-- Strategy list -->
                <div class="space-y-2">
                  <label v-for="member in suggestion.strategies" :key="member.strategy" class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer">
                    <input
                      type="radio"
                      :name="'target-' + suggestion.strategy_id"
                      :value="member.strategy"
                      v-model="suggestionTargets[suggestion.strategy_id]"
                      class="text-teal-500 focus:ring-teal-500 dark:bg-gray-800 dark:border-gray-600"
                    />
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{{ member.strategy }}</p>
                      <p class="text-xs text-gray-500">{{ member.num_bets }} bets · {{ formatDate(member.first_bet) }} – {{ formatDate(member.last_bet) }}</p>
                    </div>
                    <span v-if="suggestionTargets[suggestion.strategy_id] === member.strategy" class="text-[10px] font-semibold text-teal-500 bg-teal-500/10 border border-teal-500/20 px-2 py-0.5 rounded-full">TARGET</span>
                  </label>
                </div>

                <p class="text-xs text-gray-400 italic">
                  Select the name you want to keep. All other strategies will be renamed to the selected target.
                </p>

                <button
                  @click="startSuggestionMerge(suggestion.strategy_id)"
                  :disabled="!suggestionTargets[suggestion.strategy_id]"
                  class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-white bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-600 hover:to-sky-600 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all shadow-sm"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                  Merge into "{{ suggestionTargets[suggestion.strategy_id] }}"
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- ═══════ Manual Merge Tab ═══════ -->
    <div v-if="activeSubTab === 'manual'">
      <div class="space-y-4">
        <p class="text-xs text-gray-500">
          Select two or more strategies to merge, then choose the target name. All selected strategies will be renamed to the target.
        </p>

        <!-- Search -->
        <div class="relative max-w-sm">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="manualSearchQuery"
            type="text"
            placeholder="Search strategies…"
            class="input-field pl-10"
          />
        </div>

        <!-- Strategy table -->
        <div class="glass-card overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100 dark:border-gray-800/40">
                  <th class="px-4 py-2.5 text-left">
                    <input
                      type="checkbox"
                      @change="selectAllVisible"
                      :checked="filteredStrategies.length > 0 && selectedForMerge.size === filteredStrategies.length"
                      :indeterminate="selectedForMerge.size > 0 && selectedForMerge.size < filteredStrategies.length"
                      class="text-teal-500 focus:ring-teal-500 dark:bg-gray-800 dark:border-gray-600 rounded"
                    />
                  </th>
                  <th class="px-4 py-2.5 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Strategy</th>
                  <th class="px-4 py-2.5 text-right text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Bets</th>
                  <th class="px-4 py-2.5 text-right text-[11px] font-semibold text-gray-500 uppercase tracking-wider">P/L</th>
                  <th class="px-4 py-2.5 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Period</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredStrategies.length === 0">
                  <td colspan="5" class="px-4 py-8 text-center text-sm text-gray-500">
                    No strategies found.
                  </td>
                </tr>
                <tr
                  v-for="strat in filteredStrategies"
                  :key="strat.strategy"
                  @click="toggleManualSelect(strat.strategy)"
                  class="border-b border-gray-50 dark:border-gray-800/20 hover:bg-gray-50 dark:hover:bg-gray-800/20 cursor-pointer transition-colors"
                  :class="{ 'bg-teal-500/5 dark:bg-teal-500/5': selectedForMerge.has(strat.strategy) }"
                >
                  <td class="px-4 py-2.5">
                    <input
                      type="checkbox"
                      :checked="selectedForMerge.has(strat.strategy)"
                      @click.stop="toggleManualSelect(strat.strategy)"
                      class="text-teal-500 focus:ring-teal-500 dark:bg-gray-800 dark:border-gray-600 rounded"
                    />
                  </td>
                  <td class="px-4 py-2.5 text-sm font-medium text-gray-800 dark:text-gray-200">{{ strat.strategy }}</td>
                  <td class="px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 text-right tabular-nums">{{ strat.num_bets.toLocaleString() }}</td>
                  <td class="px-4 py-2.5 text-sm text-right tabular-nums" :class="strat.total_pl >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                    {{ formatPL(strat.total_pl) }}
                  </td>
                  <td class="px-4 py-2.5 text-xs text-gray-500 whitespace-nowrap">
                    {{ formatDate(strat.first_bet) }} – {{ formatDate(strat.last_bet) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Merge controls (show when 2+ selected) -->
        <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 translate-y-2" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 translate-y-2">
          <div v-if="selectedForMerge.size >= 2" class="glass-card p-4 space-y-3">
            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Merge {{ selectedForMerge.size }} strategies
            </h3>

            <div class="flex flex-wrap gap-1.5">
              <span v-for="strat in selectedStrategiesList" :key="strat.strategy" class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
                {{ strat.strategy }}
                <span class="text-gray-400">({{ strat.num_bets }})</span>
                <button @click.stop="toggleManualSelect(strat.strategy)" class="ml-0.5 text-gray-400 hover:text-rose-400 transition-colors">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </span>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Merge into (target name)</label>
              <div class="flex gap-2">
                <select
                  v-model="manualTargetName"
                  class="input-field flex-1"
                >
                  <option value="">— Pick an existing name or type below —</option>
                  <option v-for="strat in selectedStrategiesList" :key="strat.strategy" :value="strat.strategy">
                    {{ strat.strategy }} ({{ strat.num_bets }} bets)
                  </option>
                </select>
              </div>
              <div class="mt-2">
                <input
                  v-model="manualTargetName"
                  type="text"
                  placeholder="Or type a custom name…"
                  class="input-field"
                />
              </div>
            </div>

            <button
              @click="startManualMerge"
              :disabled="!canMerge || manualLoading"
              class="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-white bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-600 hover:to-sky-600 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all shadow-sm"
            >
              <svg v-if="!manualLoading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
              <div v-else class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              Merge into "{{ manualTargetName }}"
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ═══════ Confirm Dialogs ═══════ -->
    <ConfirmDialog
      :open="showSuggestionConfirm && !!pendingSuggestionMerge"
      title="Merge Strategies"
      :message="pendingSuggestionMerge ? `This will rename ${pendingSuggestionMerge.sources.length} strategies into '${pendingSuggestionMerge.target}'. This action cannot be undone.` : ''"
      confirm-label="Merge"
      variant="warning"
      @confirm="confirmSuggestionMerge"
      @cancel="showSuggestionConfirm = false; pendingSuggestionMerge = null"
    />

    <ConfirmDialog
      :open="showManualConfirm"
      title="Merge Strategies"
      :message="`This will merge ${selectedForMerge.size} strategies into '${manualTargetName}'. All bets from the source strategies will be renamed. This action cannot be undone.`"
      confirm-label="Merge"
      variant="warning"
      @confirm="confirmManualMerge"
      @cancel="showManualConfirm = false"
    />
  </div>
</template>

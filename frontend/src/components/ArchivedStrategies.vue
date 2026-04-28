<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBetStore } from '../stores/betStore'
import ConfirmDialog from './ConfirmDialog.vue'
import LoadingOverlay from './LoadingOverlay.vue'

const betStore = useBetStore()
const selectedStrategies = ref<Set<string>>(new Set())
const showRestoreDialog = ref(false)
const searchQuery = ref('')
const restoring = ref(false)

onMounted(() => {
  betStore.loadArchivedStrategies()
})

const filteredStrategies = computed(() => {
  if (!searchQuery.value) return betStore.archivedStrategies
  const q = searchQuery.value.toLowerCase()
  return betStore.archivedStrategies.filter((s) => s.strategy.toLowerCase().includes(q))
})

function toggleStrategy(strategy: string) {
  if (selectedStrategies.value.has(strategy)) {
    selectedStrategies.value.delete(strategy)
  } else {
    selectedStrategies.value.add(strategy)
  }
}

function toggleAll() {
  if (selectedStrategies.value.size === filteredStrategies.value.length) {
    selectedStrategies.value.clear()
  } else {
    selectedStrategies.value = new Set(filteredStrategies.value.map((s) => s.strategy))
  }
}

async function confirmRestore() {
  showRestoreDialog.value = false
  restoring.value = true
  try {
    await betStore.restoreStrategies(Array.from(selectedStrategies.value))
    selectedStrategies.value.clear()
  } finally {
    restoring.value = false
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header + controls -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">Archived Strategies</h2>
        <p class="mt-1 text-sm text-gray-500">
          Archived strategies are hidden from the main dashboard. Restore them at any time.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="showRestoreDialog = true"
          :disabled="selectedStrategies.size === 0"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Restore ({{ selectedStrategies.size }})
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="relative max-w-sm">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search archived strategies…"
        class="input-field !pl-10"
      />
    </div>

    <!-- Table -->
    <div class="glass-card !p-0 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th class="!px-4 !w-10">
                <input
                  type="checkbox"
                  :checked="selectedStrategies.size === filteredStrategies.length && filteredStrategies.length > 0"
                  @change="toggleAll"
                  class="rounded border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-white/5 text-teal-500 focus:ring-teal-500/30 focus:ring-offset-0"
                />
              </th>
              <th>Strategy</th>
              <th>Bets</th>
              <th>P/L</th>
              <th>ROI</th>
              <th>Win Rate</th>
              <th>Avg Odds</th>
              <th>First Bet</th>
              <th>Last Bet</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="stat in filteredStrategies"
              :key="stat.strategy"
            >
              <td class="!px-4">
                <input
                  type="checkbox"
                  :checked="selectedStrategies.has(stat.strategy)"
                  @change="toggleStrategy(stat.strategy)"
                  class="rounded border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-white/5 text-teal-500 focus:ring-teal-500/30 focus:ring-offset-0"
                />
              </td>
              <td class="font-medium text-gray-900 dark:text-white">{{ stat.strategy }}</td>
              <td class="font-mono text-gray-400">{{ stat.num_bets.toLocaleString() }}</td>
              <td class="font-mono font-medium" :class="stat.total_pl >= 0 ? 'text-emerald-400' : 'text-rose-400'">
                £{{ stat.total_pl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
              </td>
              <td class="font-mono" :class="stat.roi >= 0 ? 'text-emerald-400' : 'text-rose-400'">
                {{ stat.roi.toFixed(2) }}%
              </td>
              <td class="font-mono text-gray-400">{{ stat.win_rate.toFixed(1) }}%</td>
              <td class="font-mono text-gray-400">{{ stat.avg_odds.toFixed(2) }}</td>
              <td class="font-mono text-gray-500 text-xs">{{ formatDate(stat.first_bet) }}</td>
              <td class="font-mono text-gray-500 text-xs">{{ formatDate(stat.last_bet) }}</td>
            </tr>
            <tr v-if="filteredStrategies.length === 0">
              <td colspan="9" class="!py-12 text-center">
                <div class="flex flex-col items-center gap-2">
                  <svg class="w-12 h-12 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                  </svg>
                  <p class="text-sm text-gray-500">No archived strategies</p>
                  <p class="text-xs text-gray-600">Strategies you archive will appear here</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Restore Confirmation Dialog -->
    <ConfirmDialog
      :open="showRestoreDialog"
      title="Restore Strategies"
      :message="`Are you sure you want to restore ${selectedStrategies.size} strateg${selectedStrategies.size === 1 ? 'y' : 'ies'} and all their bets back to the main dashboard?`"
      confirm-label="Restore"
      cancel-label="Cancel"
      variant="info"
      icon="restore"
      @confirm="confirmRestore"
      @cancel="showRestoreDialog = false"
    />

    <LoadingOverlay
      :show="restoring"
      title="Restoring strategies…"
      message="Returning the selected strategies to the dashboard and recalculating stats. This can take up to a minute for large data sets — please wait."
    />
  </div>
</template>

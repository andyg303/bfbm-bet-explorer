<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBetStore } from '../stores/betStore'
import ConfirmDialog from './ConfirmDialog.vue'

const betStore = useBetStore()
const selectedStrategies = ref<Set<string>>(new Set())
const showRestoreDialog = ref(false)
const searchQuery = ref('')

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
  await betStore.restoreStrategies(Array.from(selectedStrategies.value))
  selectedStrategies.value.clear()
  showRestoreDialog.value = false
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
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">Archived Strategies</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          These strategies have been archived and are hidden from the main dashboard. You can restore them at any time.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="showRestoreDialog = true"
          :disabled="selectedStrategies.size === 0"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg transition-colors"
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
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search archived strategies…"
        class="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      />
    </div>

    <!-- Table -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm ring-1 ring-gray-200 dark:ring-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              <th class="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  :checked="selectedStrategies.size === filteredStrategies.length && filteredStrategies.length > 0"
                  @change="toggleAll"
                  class="rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500"
                />
              </th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Strategy</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Bets</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">P/L</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">ROI</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Win Rate</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Avg Odds</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">First Bet</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Bet</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="stat in filteredStrategies"
              :key="stat.strategy"
              class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <td class="px-4 py-4">
                <input
                  type="checkbox"
                  :checked="selectedStrategies.has(stat.strategy)"
                  @change="toggleStrategy(stat.strategy)"
                  class="rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500"
                />
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{{ stat.strategy }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.num_bets.toLocaleString() }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium" :class="stat.total_pl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                £{{ stat.total_pl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm" :class="stat.roi >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stat.roi.toFixed(2) }}%
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.win_rate.toFixed(1) }}%</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.avg_odds.toFixed(2) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ formatDate(stat.first_bet) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ formatDate(stat.last_bet) }}</td>
            </tr>
            <tr v-if="filteredStrategies.length === 0">
              <td colspan="9" class="px-6 py-12 text-center">
                <div class="flex flex-col items-center gap-2">
                  <svg class="w-12 h-12 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                  </svg>
                  <p class="text-sm text-gray-500 dark:text-gray-400">No archived strategies</p>
                  <p class="text-xs text-gray-400 dark:text-gray-500">Strategies you archive will appear here</p>
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
  </div>
</template>

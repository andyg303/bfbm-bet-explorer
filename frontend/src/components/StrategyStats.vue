<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBetStore } from '../stores/betStore'
import type { StrategyStats } from '../services/api'
import StrategyFilters from './StrategyFilters.vue'
import ConfirmDialog from './ConfirmDialog.vue'

const betStore = useBetStore()

const sortKey = ref<keyof StrategyStats>('total_pl')
const sortDirection = ref<'asc' | 'desc'>('desc')
const selectedStrategies = ref<Set<string>>(new Set())
const showArchiveDialog = ref(false)

const strategyFilters = ref({
  nameSearch: '',
  minBets: null as number | null,
  maxBets: null as number | null,
  minPL: null as number | null,
  maxPL: null as number | null,
  minROI: null as number | null,
  maxROI: null as number | null,
  minWinRate: null as number | null,
  maxWinRate: null as number | null,
  minBspFill: null as number | null,
  maxBspFill: null as number | null
})

const stats = computed(() => {
  const data = betStore.strategyStats || []
  if (!data.length) return data
  
  // Apply frontend filters
  let filtered = data
  
  // Name search
  if (strategyFilters.value.nameSearch) {
    const search = strategyFilters.value.nameSearch.toLowerCase()
    filtered = filtered.filter(stat => stat.strategy.toLowerCase().includes(search))
  }
  
  // Bets range
  if (strategyFilters.value.minBets !== null) {
    filtered = filtered.filter(stat => stat.num_bets >= strategyFilters.value.minBets!)
  }
  if (strategyFilters.value.maxBets !== null) {
    filtered = filtered.filter(stat => stat.num_bets <= strategyFilters.value.maxBets!)
  }
  
  // P/L range
  if (strategyFilters.value.minPL !== null) {
    filtered = filtered.filter(stat => stat.total_pl >= strategyFilters.value.minPL!)
  }
  if (strategyFilters.value.maxPL !== null) {
    filtered = filtered.filter(stat => stat.total_pl <= strategyFilters.value.maxPL!)
  }
  
  // ROI range
  if (strategyFilters.value.minROI !== null) {
    filtered = filtered.filter(stat => stat.roi >= strategyFilters.value.minROI!)
  }
  if (strategyFilters.value.maxROI !== null) {
    filtered = filtered.filter(stat => stat.roi <= strategyFilters.value.maxROI!)
  }
  
  // Win Rate range
  if (strategyFilters.value.minWinRate !== null) {
    filtered = filtered.filter(stat => stat.win_rate >= strategyFilters.value.minWinRate!)
  }
  if (strategyFilters.value.maxWinRate !== null) {
    filtered = filtered.filter(stat => stat.win_rate <= strategyFilters.value.maxWinRate!)
  }
  
  // BSP Fill % range
  if (strategyFilters.value.minBspFill !== null) {
    filtered = filtered.filter(stat => stat.bsp_fill_pct >= strategyFilters.value.minBspFill!)
  }
  if (strategyFilters.value.maxBspFill !== null) {
    filtered = filtered.filter(stat => stat.bsp_fill_pct <= strategyFilters.value.maxBspFill!)
  }
  
  // Sort the filtered data
  const sorted = [...filtered].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    
    // Handle string comparison
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection.value === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }
    
    // Handle numeric comparison
    const aNum = Number(aVal) || 0
    const bNum = Number(bVal) || 0
    return sortDirection.value === 'asc' ? aNum - bNum : bNum - aNum
  })
  
  return sorted
})

function sort(key: keyof StrategyStats) {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'desc'
  }
}

function toggleStrategy(strategy: string) {
  if (selectedStrategies.value.has(strategy)) {
    selectedStrategies.value.delete(strategy)
  } else {
    selectedStrategies.value.add(strategy)
  }
}

function toggleAll() {
  if (selectedStrategies.value.size === stats.value.length) {
    selectedStrategies.value.clear()
  } else {
    selectedStrategies.value = new Set(stats.value.map(s => s.strategy))
  }
}

function applySelection() {
  betStore.filters.strategies = Array.from(selectedStrategies.value)
}

function clearSelection() {
  selectedStrategies.value.clear()
  betStore.stakingParams = {
    staking_type: 'default',
    base_stake: 10,
  }
  betStore.filters.strategies = []
  betStore.refreshAll()
}

function clearFilters() {
  betStore.stakingParams = {
    staking_type: 'default',
    base_stake: 10,
  }
  strategyFilters.value = {
    nameSearch: '',
    minBets: null,
    maxBets: null,
    minPL: null,
    maxPL: null,
    minROI: null,
    maxROI: null,
    minWinRate: null,
    maxWinRate: null,
    minBspFill: null,
    maxBspFill: null
  }
}

async function archiveSelected() {
  await betStore.archiveStrategies(Array.from(selectedStrategies.value))
  selectedStrategies.value.clear()
  showArchiveDialog.value = false
}
</script>

<template>
  <div class="glass-card">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-white/5">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
            <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 class="text-base font-semibold text-white tracking-tight">Strategy Performance</h2>
        </div>
        <div class="flex gap-2">
          <button 
            @click="showArchiveDialog = true" 
            :disabled="selectedStrategies.size === 0"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            Archive ({{ selectedStrategies.size }})
          </button>
          <button 
            @click="applySelection" 
            :disabled="selectedStrategies.size === 0"
            class="px-3 py-1.5 text-xs font-medium text-teal-400 bg-teal-500/10 border border-teal-500/20 hover:bg-teal-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
          >
            Apply ({{ selectedStrategies.size }})
          </button>
          <button 
            @click="clearSelection" 
            class="px-3 py-1.5 text-xs font-medium text-gray-400 bg-white/5 border border-white/10 hover:bg-white/10 rounded-lg transition-all"
          >
            Clear
          </button>
        </div>
      </div>
      <StrategyFilters v-model="strategyFilters" @clear="clearFilters" />
    </div>
    
    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th class="!px-4 !w-10">
              <input 
                type="checkbox" 
                :checked="selectedStrategies.size === stats.length && stats.length > 0"
                @change="toggleAll"
                class="rounded border-gray-600 bg-white/5 text-teal-500 focus:ring-teal-500/30 focus:ring-offset-0"
              >
            </th>
            <th @click="sort('strategy')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Strategy <span v-if="sortKey === 'strategy'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('num_bets')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Bets <span v-if="sortKey === 'num_bets'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('total_pl')" class="cursor-pointer hover:text-teal-400 transition-colors">
              P/L <span v-if="sortKey === 'total_pl'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('roi')" class="cursor-pointer hover:text-teal-400 transition-colors">
              ROI % <span v-if="sortKey === 'roi'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('yield_pct')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Yield <span v-if="sortKey === 'yield_pct'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('total_staked')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Staked <span v-if="sortKey === 'total_staked'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_odds')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Avg Odds <span v-if="sortKey === 'avg_odds'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('win_rate')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Win Rate <span v-if="sortKey === 'win_rate'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th>Back/Lay</th>
            <th @click="sort('bsp_fill_pct')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP Fill % <span v-if="sortKey === 'bsp_fill_pct'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_abs')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP Abs <span v-if="sortKey === 'avg_bsp_abs'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_pct')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP % <span v-if="sortKey === 'avg_bsp_pct'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_prob')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP Prob <span v-if="sortKey === 'avg_bsp_prob'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stat in stats" :key="stat.strategy">
            <td class="!px-4">
              <input 
                type="checkbox" 
                :checked="selectedStrategies.has(stat.strategy)"
                @change="toggleStrategy(stat.strategy)"
                class="rounded border-gray-600 bg-white/5 text-teal-500 focus:ring-teal-500/30 focus:ring-offset-0"
              >
            </td>
            <td class="font-medium text-white">{{ stat.strategy }}</td>
            <td class="font-mono">{{ stat.num_bets }}</td>
            <td class="font-mono font-medium" :class="stat.total_pl >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              £{{ stat.total_pl.toLocaleString() }}
            </td>
            <td class="font-mono" :class="stat.roi >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ stat.roi }}%
            </td>
            <td class="font-mono" :class="stat.yield_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ stat.yield_pct.toFixed(2) }}%
            </td>
            <td class="font-mono text-gray-400">£{{ stat.total_staked.toLocaleString() }}</td>
            <td class="font-mono text-gray-400">{{ stat.avg_odds.toFixed(2) }}</td>
            <td class="font-mono text-gray-400">{{ stat.win_rate.toFixed(1) }}%</td>
            <td class="font-mono text-gray-400">{{ stat.num_back }}/{{ stat.num_lay }}</td>
            <td class="font-mono text-gray-400">{{ stat.bsp_fill_pct.toFixed(1) }}%</td>
            <td class="font-mono" :class="stat.avg_bsp_abs >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ stat.avg_bsp_abs > 0 ? '+' : '' }}{{ stat.avg_bsp_abs.toFixed(3) }}
            </td>
            <td class="font-mono" :class="stat.avg_bsp_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ stat.avg_bsp_pct > 0 ? '+' : '' }}{{ stat.avg_bsp_pct.toFixed(2) }}%
            </td>
            <td class="font-mono" :class="stat.avg_bsp_prob >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ stat.avg_bsp_prob > 0 ? '+' : '' }}{{ stat.avg_bsp_prob.toFixed(2) }}%
            </td>
          </tr>
          <tr v-if="!stats || stats.length === 0">
            <td colspan="14" class="!py-12 text-center text-sm text-gray-500">No strategies match the filters</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Archive Confirmation Dialog -->
    <ConfirmDialog
      :open="showArchiveDialog"
      title="Archive Strategies"
      :message="`Are you sure you want to archive ${selectedStrategies.size} strateg${selectedStrategies.size === 1 ? 'y' : 'ies'}? All bets within ${selectedStrategies.size === 1 ? 'it' : 'them'} will be hidden from the dashboard. You can restore them at any time from the Archive.`"
      confirm-label="Archive"
      cancel-label="Cancel"
      variant="warning"
      icon="archive"
      @confirm="archiveSelected"
      @cancel="showArchiveDialog = false"
    />
  </div>
</template>

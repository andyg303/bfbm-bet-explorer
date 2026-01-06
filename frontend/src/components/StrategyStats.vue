<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBetStore } from '../stores/betStore'
import type { StrategyStats } from '../services/api'
import StrategyFilters from './StrategyFilters.vue'

const betStore = useBetStore()

const sortKey = ref<keyof StrategyStats>('total_pl')
const sortDirection = ref<'asc' | 'desc'>('desc')
const selectedStrategies = ref<Set<string>>(new Set())

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
  betStore.filters.strategies = []
}

function clearFilters() {
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
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Strategy Performance</h2>
        <div class="flex gap-2">
          <button 
            @click="applySelection" 
            :disabled="selectedStrategies.size === 0"
            class="px-3 py-1 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded"
          >
            Apply Selection ({{ selectedStrategies.size }})
          </button>
          <button 
            @click="clearSelection" 
            class="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded"
          >
            Clear
          </button>
        </div>
      </div>
      <StrategyFilters v-model="strategyFilters" @clear="clearFilters" />
    </div>
    
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th class="px-4 py-3 text-left">
              <input 
                type="checkbox" 
                :checked="selectedStrategies.size === stats.length && stats.length > 0"
                @change="toggleAll"
                class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              >
            </th>
            <th @click="sort('strategy')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
              Strategy <span v-if="sortKey === 'strategy'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('num_bets')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              Bets <span v-if="sortKey === 'num_bets'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('total_pl')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              P/L <span v-if="sortKey === 'total_pl'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('roi')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              ROI % <span v-if="sortKey === 'roi'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('yield_pct')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              Yield <span v-if="sortKey === 'yield_pct'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('total_staked')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              Staked <span v-if="sortKey === 'total_staked'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_odds')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              Avg Odds <span v-if="sortKey === 'avg_odds'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('win_rate')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
              Win Rate <span v-if="sortKey === 'win_rate'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Back/Lay</th>
            <th @click="sort('bsp_fill_pct')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
              BSP Fill % <span v-if="sortKey === 'bsp_fill_pct'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_abs')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
              BSP Abs <span v-if="sortKey === 'avg_bsp_abs'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_pct')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
              BSP % <span v-if="sortKey === 'avg_bsp_pct'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_prob')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
              BSP Prob <span v-if="sortKey === 'avg_bsp_prob'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="stat in stats" :key="stat.strategy" class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-4">
              <input 
                type="checkbox" 
                :checked="selectedStrategies.has(stat.strategy)"
                @change="toggleStrategy(stat.strategy)"
                class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              >
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{{ stat.strategy }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.num_bets }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium" :class="stat.total_pl >= 0 ? 'text-green-600' : 'text-red-600'">
              £{{ stat.total_pl.toLocaleString() }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="stat.roi >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ stat.roi }}%
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">£{{ stat.yield_pct.toFixed(2) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">£{{ stat.total_staked.toLocaleString() }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.avg_odds.toFixed(2) }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.win_rate.toFixed(1) }}%</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.num_back }}/{{ stat.num_lay }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ stat.bsp_fill_pct.toFixed(1) }}%</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="stat.avg_bsp_abs >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ stat.avg_bsp_abs > 0 ? '+' : '' }}{{ stat.avg_bsp_abs.toFixed(3) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="stat.avg_bsp_pct >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ stat.avg_bsp_pct > 0 ? '+' : '' }}{{ stat.avg_bsp_pct.toFixed(2) }}%
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm" :class="stat.avg_bsp_prob >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ stat.avg_bsp_prob > 0 ? '+' : '' }}{{ stat.avg_bsp_prob.toFixed(2) }}%
            </td>
          </tr>
          <tr v-if="!stats || stats.length === 0">
            <td colspan="14" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">No strategies match the filters</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

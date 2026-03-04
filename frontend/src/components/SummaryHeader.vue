<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const stats = computed(() => betStore.summaryStats || {
  num_bets: 0,
  total_pl: 0,
  total_staked: 0,
  roi: 0,
  yield_pct: 0,
  avg_odds: 0,
  win_rate: 0
})

const numStrategies = computed(() => betStore.strategyStats?.length || 0)
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-6 gap-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Bets</div>
      <div class="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{{ (stats.num_bets || 0).toLocaleString() }}</div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total P/L</div>
      <div class="mt-2 text-3xl font-semibold" :class="(stats.total_pl || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
        £{{ (stats.total_pl || 0).toLocaleString() }}
      </div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Staked</div>
      <div class="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">£{{ (stats.total_staked || 0).toLocaleString() }}</div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">ROI</div>
      <div class="mt-2 text-3xl font-semibold" :class="(stats.roi || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
        {{ (stats.roi || 0) }}%
      </div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Yield</div>
      <div class="mt-2 text-3xl font-semibold" :class="(stats.yield_pct || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
        {{ (stats.yield_pct || 0) }}%
      </div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Strategies</div>
      <div class="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{{ numStrategies }}</div>
    </div>
  </div>
</template>

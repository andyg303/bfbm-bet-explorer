<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const stats = computed(() => betStore.summaryStats || {
  total_bets: 0,
  total_pl: 0,
  total_staked: 0,
  roi: 0,
  num_strategies: 0
})
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Bets</div>
      <div class="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{{ stats.total_bets.toLocaleString() }}</div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total P/L</div>
      <div class="mt-2 text-3xl font-semibold" :class="stats.total_pl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
        £{{ stats.total_pl.toLocaleString() }}
      </div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Staked</div>
      <div class="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">£{{ stats.total_staked.toLocaleString() }}</div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">ROI</div>
      <div class="mt-2 text-3xl font-semibold" :class="stats.roi >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
        {{ stats.roi }}%
      </div>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Strategies</div>
      <div class="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{{ stats.num_strategies }}</div>
    </div>
  </div>
</template>

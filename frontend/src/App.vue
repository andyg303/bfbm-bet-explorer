<script setup lang="ts">
import { onMounted } from 'vue'
import { useBetStore } from './stores/betStore'
import { useDarkMode } from './composables/useDarkMode'
import FilterPanel from './components/FilterPanel.vue'
import StrategyStats from './components/StrategyStats.vue'
import BetTable from './components/BetTable.vue'
import Charts from './components/Charts.vue'
import OddsBandsChart from './components/OddsBandsChart.vue'
import StakingCalculator from './components/StakingCalculator.vue'
import SummaryHeader from './components/SummaryHeader.vue'
import IngestData from './components/IngestData.vue'

const betStore = useBetStore()
const { isDark, toggle } = useDarkMode()

onMounted(async () => {
  await betStore.loadFilterOptions()
  await betStore.loadSummaryStats()
  await betStore.refreshAll()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
    <header class="bg-white dark:bg-gray-800 shadow-sm">
      <div class="px-4 py-6 sm:px-6 lg:px-8 flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">BFBM Bet Explorer</h1>
        <div class="flex items-center gap-3">
          <IngestData />
          <button 
          @click="toggle" 
          class="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        >
          <svg v-if="!isDark" class="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
          <svg v-else class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </button>
        </div>
      </div>
    </header>

    <main class="px-4 py-6 sm:px-6 lg:px-8">
      <SummaryHeader />
      
      <div class="mt-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div class="lg:col-span-1">
          <FilterPanel />
          <div class="mt-6">
            <StakingCalculator />
          </div>
        </div>
        
        <div class="lg:col-span-3 space-y-6">
          <StrategyStats />
          <Charts />
          <OddsBandsChart />
          <BetTable />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped></style>

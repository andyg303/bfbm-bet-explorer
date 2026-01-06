<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  modelValue: {
    nameSearch: string
    minBets: number | null
    maxBets: number | null
    minPL: number | null
    maxPL: number | null
    minROI: number | null
    maxROI: number | null
    minWinRate: number | null
    maxWinRate: number | null
    minBspFill: number | null
    maxBspFill: number | null
  }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: typeof props.modelValue]
  'clear': []
}>()

const localFilters = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function clearFilters() {
  emit('clear')
}
</script>

<template>
  <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Strategy Filters</h3>
      <button @click="clearFilters" class="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
        Clear Filters
      </button>
    </div>
    
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
      <!-- Name Search -->
      <div class="col-span-2">
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Strategy Name</label>
        <input 
          v-model="localFilters.nameSearch" 
          type="text" 
          placeholder="Search..."
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>

      <!-- Bets Range -->
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Min Bets</label>
        <input 
          v-model.number="localFilters.minBets" 
          type="number" 
          placeholder="Min"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Max Bets</label>
        <input 
          v-model.number="localFilters.maxBets" 
          type="number" 
          placeholder="Max"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>

      <!-- P/L Range -->
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Min P/L (£)</label>
        <input 
          v-model.number="localFilters.minPL" 
          type="number" 
          step="0.01"
          placeholder="Min"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Max P/L (£)</label>
        <input 
          v-model.number="localFilters.maxPL" 
          type="number" 
          step="0.01"
          placeholder="Max"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>

      <!-- ROI Range -->
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Min ROI %</label>
        <input 
          v-model.number="localFilters.minROI" 
          type="number" 
          step="0.1"
          placeholder="Min"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Max ROI %</label>
        <input 
          v-model.number="localFilters.maxROI" 
          type="number" 
          step="0.1"
          placeholder="Max"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>

      <!-- Win Rate Range -->
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Min Win %</label>
        <input 
          v-model.number="localFilters.minWinRate" 
          type="number" 
          step="0.1"
          placeholder="Min"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Max Win %</label>
        <input 
          v-model.number="localFilters.maxWinRate" 
          type="number" 
          step="0.1"
          placeholder="Max"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>

      <!-- BSP Fill % Range -->
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Min BSP Fill %</label>
        <input 
          v-model.number="localFilters.minBspFill" 
          type="number" 
          step="0.1"
          placeholder="Min"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Max BSP Fill %</label>
        <input 
          v-model.number="localFilters.maxBspFill" 
          type="number" 
          step="0.1"
          placeholder="Max"
          class="w-full border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
        >
      </div>
    </div>
  </div>
</template>

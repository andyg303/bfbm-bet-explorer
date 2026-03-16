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
  <div class="rounded-lg bg-gray-50 dark:bg-white/[0.02] border border-gray-200 dark:border-white/5 p-4 mb-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Strategy Filters</h3>
      <button @click="clearFilters" class="text-xs text-teal-400 hover:text-teal-300 transition-colors">
        Clear Filters
      </button>
    </div>
    
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
      <!-- Name Search -->
      <div class="col-span-2">
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Strategy Name</label>
        <input 
          v-model="localFilters.nameSearch" 
          type="text" 
          placeholder="Search..."
          class="input-field !py-1 !text-xs"
        >
      </div>

      <!-- Bets Range -->
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Min Bets</label>
        <input 
          v-model.number="localFilters.minBets" 
          type="number" 
          placeholder="Min"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Max Bets</label>
        <input 
          v-model.number="localFilters.maxBets" 
          type="number" 
          placeholder="Max"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>

      <!-- P/L Range -->
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Min P/L (£)</label>
        <input 
          v-model.number="localFilters.minPL" 
          type="number" 
          step="0.01"
          placeholder="Min"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Max P/L (£)</label>
        <input 
          v-model.number="localFilters.maxPL" 
          type="number" 
          step="0.01"
          placeholder="Max"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>

      <!-- ROI Range -->
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Min ROI %</label>
        <input 
          v-model.number="localFilters.minROI" 
          type="number" 
          step="0.1"
          placeholder="Min"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Max ROI %</label>
        <input 
          v-model.number="localFilters.maxROI" 
          type="number" 
          step="0.1"
          placeholder="Max"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>

      <!-- Win Rate Range -->
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Min Win %</label>
        <input 
          v-model.number="localFilters.minWinRate" 
          type="number" 
          step="0.1"
          placeholder="Min"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Max Win %</label>
        <input 
          v-model.number="localFilters.maxWinRate" 
          type="number" 
          step="0.1"
          placeholder="Max"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>

      <!-- BSP Fill % Range -->
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Min BSP Fill %</label>
        <input 
          v-model.number="localFilters.minBspFill" 
          type="number" 
          step="0.1"
          placeholder="Min"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>
      <div>
        <label class="block text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">Max BSP Fill %</label>
        <input 
          v-model.number="localFilters.maxBspFill" 
          type="number" 
          step="0.1"
          placeholder="Max"
          class="input-field !py-1 !text-xs font-mono"
        >
      </div>
    </div>
  </div>
</template>

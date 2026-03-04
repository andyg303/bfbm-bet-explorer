<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const options = computed(() => betStore.filterOptions || {
  strategies: [],
  bet_types: [],
  statuses: [],
  market_types: [],
  country_codes: [],
  events: []
})

watch(() => betStore.filters, () => {
  betStore.refreshAll()
}, { deep: true })

function clearFilters() {
  betStore.stakingParams = {
    staking_type: 'default',
    base_stake: 10,
  }
  betStore.filters = {
    strategies: [],
    bet_types: [],
    statuses: [],
    market_types: [],
    country_codes: [],
    events: [],
  }
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Filters</h2>
      <button @click="clearFilters" class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">Clear All</button>
    </div>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Bet Type</label>
        <select v-model="betStore.filters.bet_types" multiple class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option v-for="type in options.bet_types" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Market Type</label>
        <select v-model="betStore.filters.market_types" multiple class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option v-for="market in options.market_types" :key="market" :value="market">{{ market }}</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Event Type</label>
        <select v-model="betStore.filters.events" multiple class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option v-for="event in options.events" :key="event" :value="event">{{ event }}</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Odds Range</label>
        <div class="grid grid-cols-2 gap-2">
          <input v-model.number="betStore.filters.min_odds" type="number" step="0.1" placeholder="Min" class="border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
          <input v-model.number="betStore.filters.max_odds" type="number" step="0.1" placeholder="Max" class="border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Stake Range (£)</label>
        <div class="grid grid-cols-2 gap-2">
          <input v-model.number="betStore.filters.min_stake" type="number" step="0.01" placeholder="Min" class="border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
          <input v-model.number="betStore.filters.max_stake" type="number" step="0.01" placeholder="Max" class="border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">P/L Range (£)</label>
        <div class="grid grid-cols-2 gap-2">
          <input v-model.number="betStore.filters.min_pl" type="number" step="0.01" placeholder="Min" class="border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
          <input v-model.number="betStore.filters.max_pl" type="number" step="0.01" placeholder="Max" class="border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Date Range</label>
        <div class="space-y-2">
          <input v-model="betStore.filters.date_from" type="date" class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <input v-model="betStore.filters.date_to" type="date" class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Selection Search</label>
        <input v-model="betStore.filters.selection_search" type="text" placeholder="Search selection..." class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description Search</label>
        <input v-model="betStore.filters.description_search" type="text" placeholder="Search description..." class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500">
      </div>
    </div>
  </div>
</template>

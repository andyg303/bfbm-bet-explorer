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
  <div class="glass-card p-5">
    <div class="flex justify-between items-center mb-5">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
        <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
        Filters
      </h2>
      <button @click="clearFilters" class="text-xs text-teal-400 hover:text-teal-300 font-medium transition-colors">Clear All</button>
    </div>

    <div class="space-y-4">
      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Bet Type</label>
        <select v-model="betStore.filters.bet_types" multiple class="input-field !py-1.5 text-xs" style="min-height: 60px;">
          <option v-for="type in options.bet_types" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Market Type</label>
        <select v-model="betStore.filters.market_types" multiple class="input-field !py-1.5 text-xs" style="min-height: 60px;">
          <option v-for="market in options.market_types" :key="market" :value="market">{{ market }}</option>
        </select>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Event Type</label>
        <select v-model="betStore.filters.events" multiple class="input-field !py-1.5 text-xs" style="min-height: 60px;">
          <option v-for="event in options.events" :key="event" :value="event">{{ event }}</option>
        </select>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Odds Range</label>
        <div class="grid grid-cols-2 gap-2">
          <input v-model.number="betStore.filters.min_odds" type="number" step="0.1" placeholder="Min" class="input-field text-xs">
          <input v-model.number="betStore.filters.max_odds" type="number" step="0.1" placeholder="Max" class="input-field text-xs">
        </div>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Stake Range (£)</label>
        <div class="grid grid-cols-2 gap-2">
          <input v-model.number="betStore.filters.min_stake" type="number" step="0.01" placeholder="Min" class="input-field text-xs">
          <input v-model.number="betStore.filters.max_stake" type="number" step="0.01" placeholder="Max" class="input-field text-xs">
        </div>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">P/L Range (£)</label>
        <div class="grid grid-cols-2 gap-2">
          <input v-model.number="betStore.filters.min_pl" type="number" step="0.01" placeholder="Min" class="input-field text-xs">
          <input v-model.number="betStore.filters.max_pl" type="number" step="0.01" placeholder="Max" class="input-field text-xs">
        </div>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Date Range</label>
        <div class="space-y-2">
          <input v-model="betStore.filters.date_from" type="date" class="input-field text-xs">
          <input v-model="betStore.filters.date_to" type="date" class="input-field text-xs">
        </div>
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Selection Search</label>
        <input v-model="betStore.filters.selection_search" type="text" placeholder="Search selection..." class="input-field text-xs">
      </div>

      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Description Search</label>
        <input v-model="betStore.filters.description_search" type="text" placeholder="Search description..." class="input-field text-xs">
      </div>
    </div>
  </div>
</template>

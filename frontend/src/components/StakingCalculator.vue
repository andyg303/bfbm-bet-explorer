<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const stakingTypes = [
  { value: 'default', label: 'Default (Original Stakes)' },
  { value: 'level_stake', label: 'Level Stake' },
  { value: 'level_win', label: 'Level Win' },
]

async function handleRecalculate() {
  await betStore.recalculateWithStaking()
  await betStore.refreshAll()
}

const recalcStats = computed(() => betStore.recalculatedStats?.summary || null)
</script>

<template>
  <div class="glass-card p-5">
    <h2 class="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2 mb-5">
      <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
      Staking Calculator
    </h2>

    <div class="space-y-4">
      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Staking Type</label>
        <select v-model="betStore.stakingParams.staking_type" class="input-field text-xs">
          <option v-for="type in stakingTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
        </select>
      </div>

      <div v-if="betStore.stakingParams.staking_type !== 'default'">
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Base Stake (£)</label>
        <input v-model.number="betStore.stakingParams.base_stake" type="number" step="1" min="1" class="input-field text-xs">
      </div>

      <button @click="handleRecalculate" class="w-full btn-glow !py-2.5 text-sm">Recalculate</button>

      <div v-if="recalcStats" class="mt-4 pt-4 border-t border-gray-800/60 space-y-2.5">
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">New P/L:</span>
          <span class="font-bold font-mono" :class="(recalcStats.total_pl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">£{{ (recalcStats.total_pl || 0).toLocaleString() }}</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">New Staked:</span>
          <span class="font-bold font-mono text-white">£{{ (recalcStats.total_staked || 0).toLocaleString() }}</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">New ROI:</span>
          <span class="font-bold font-mono" :class="(recalcStats.roi || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">{{ (recalcStats.roi || 0) }}%</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">Bets Analyzed:</span>
          <span class="font-bold font-mono text-white">{{ (recalcStats.num_bets || 0).toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

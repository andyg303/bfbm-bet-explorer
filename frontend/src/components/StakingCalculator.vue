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

const recalcStats = computed(() => betStore.recalculatedStats)
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Staking Calculator</h2>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Staking Type</label>
        <select v-model="betStore.stakingParams.staking_type" class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option v-for="type in stakingTypes" :key="type.value" :value="type.value">
            {{ type.label }}
          </option>
        </select>
      </div>

      <div v-if="betStore.stakingParams.staking_type !== 'default'">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Base Stake (£)</label>
        <input v-model.number="betStore.stakingParams.base_stake" type="number" step="1" min="1" class="w-full border border-gray-300 dark:border-gray-600 rounded-md p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
      </div>

      <button @click="handleRecalculate" class="w-full bg-blue-600 dark:bg-blue-500 text-white rounded-md py-2 px-4 hover:bg-blue-700 dark:hover:bg-blue-600 text-sm font-medium">
        Recalculate
      </button>

      <div v-if="recalcStats" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        <div class="flex justify-between text-sm">
          <span class="text-gray-600 dark:text-gray-400">New P/L:</span>
          <span class="font-semibold" :class="recalcStats.total_pl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
            £{{ recalcStats.total_pl.toLocaleString() }}
          </span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600 dark:text-gray-400">New Staked:</span>
          <span class="font-semibold text-gray-900 dark:text-white">£{{ recalcStats.total_staked.toLocaleString() }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600 dark:text-gray-400">New ROI:</span>
          <span class="font-semibold" :class="recalcStats.roi >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
            {{ recalcStats.roi }}%
          </span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600 dark:text-gray-400">Bets Analyzed:</span>
          <span class="font-semibold text-gray-900 dark:text-white">{{ recalcStats.num_bets.toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

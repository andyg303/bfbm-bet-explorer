<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()
const showHelp = ref(false)
const recalculating = ref(false)

const stakingTypes = [
  { value: 'default', label: 'Default (Original Stakes)' },
  { value: 'level_stake', label: 'Level Stake' },
  { value: 'level_win', label: 'Level Win' },
]

// Reset deduplicate when switching back to default
watch(() => betStore.stakingParams.staking_type, (val) => {
  if (val === 'default') {
    betStore.stakingParams.deduplicate = false
  }
})

async function handleRecalculate() {
  recalculating.value = true
  try {
    await betStore.recalculateWithStaking()
    await betStore.refreshAll()
  } finally {
    recalculating.value = false
  }
}

const isCustomStaking = computed(() => betStore.stakingParams.staking_type !== 'default')
const recalcStats = computed(() => betStore.recalculatedStats?.summary || null)
</script>

<template>
  <div class="glass-card p-5">
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
        <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
        Staking Calculator
      </h2>
      <button @click="showHelp = !showHelp" class="p-1 rounded-full text-gray-400 hover:text-teal-400 hover:bg-teal-500/10 transition-colors" title="Help &amp; Info">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      </button>
    </div>

    <!-- Help panel -->
    <transition name="help-slide">
      <div v-if="showHelp" class="mb-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700/50 text-xs text-gray-600 dark:text-gray-400 space-y-2.5">
        <p class="font-medium text-gray-700 dark:text-gray-300">Re-analyse your betting data with different staking strategies to see how results would have differed.</p>

        <div>
          <p class="font-semibold text-gray-700 dark:text-gray-300 mb-1">Staking Types</p>
          <ul class="space-y-1 ml-3 list-disc">
            <li><span class="font-medium text-gray-700 dark:text-gray-300">Default</span> — Uses the original stakes from your bet data as-is.</li>
            <li><span class="font-medium text-gray-700 dark:text-gray-300">Level Stake</span> — Every bet uses the same fixed stake, regardless of odds. Set your amount in the Base Stake field.</li>
            <li><span class="font-medium text-gray-700 dark:text-gray-300">Level Win</span> — For BACK bets, uses the base stake. For LAY bets, the stake is adjusted so you win a fixed amount equal to the base stake if the selection loses.</li>
          </ul>
        </div>

        <div>
          <p class="font-semibold text-gray-700 dark:text-gray-300 mb-1">Deduplicate Bets</p>
          <p>When multiple strategies trigger bets on the same market selection (e.g. backing the same horse in the same race), your results may count overlapping bets more than once. Enable deduplication to count each unique market bet only once — keeping whichever bet was placed earliest.</p>
          <p class="mt-1">A <span class="font-medium text-teal-500"># Strats</span> column appears in the bet table showing how many strategies originally triggered each bet, helping you understand overlap between your strategies.</p>
        </div>

        <p class="text-[10px] text-gray-500 italic">Click Recalculate to apply. All stats, charts, and the bet table update accordingly.</p>
      </div>
    </transition>

    <div class="space-y-4">
      <div>
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Staking Type</label>
        <select v-model="betStore.stakingParams.staking_type" class="input-field text-xs">
          <option v-for="type in stakingTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
        </select>
      </div>

      <div v-if="isCustomStaking">
        <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Base Stake (£)</label>
        <input v-model.number="betStore.stakingParams.base_stake" type="number" step="1" min="1" class="input-field text-xs">
      </div>

      <!-- Deduplicate toggle — only when not on default stakes -->
      <label v-if="isCustomStaking" class="flex items-center gap-2.5 cursor-pointer group">
        <div class="relative">
          <input type="checkbox" v-model="betStore.stakingParams.deduplicate" class="sr-only peer">
          <div class="w-9 h-5 bg-gray-200 dark:bg-gray-700 rounded-full peer-checked:bg-teal-500 transition-colors"></div>
          <div class="absolute left-0.5 top-0.5 bg-white w-4 h-4 rounded-full shadow transition-transform peer-checked:translate-x-4"></div>
        </div>
        <span class="text-xs text-gray-500 group-hover:text-gray-700 dark:group-hover:text-gray-300 transition-colors select-none">Deduplicate bets</span>
      </label>

      <button @click="handleRecalculate" class="w-full btn-glow !py-2.5 text-sm">Recalculate</button>

      <div v-if="recalcStats" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800/60 space-y-2.5">
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">New P/L:</span>
          <span class="font-bold font-mono" :class="(recalcStats.total_pl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">£{{ (recalcStats.total_pl || 0).toLocaleString() }}</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">New Staked:</span>
          <span class="font-bold font-mono text-gray-900 dark:text-white">£{{ (recalcStats.total_staked || 0).toLocaleString() }}</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">New ROI:</span>
          <span class="font-bold font-mono" :class="(recalcStats.roi || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">{{ (recalcStats.roi || 0) }}%</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">Bets Analyzed:</span>
          <span class="font-bold font-mono text-gray-900 dark:text-white">{{ (recalcStats.num_bets || 0).toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Fullscreen recalculating overlay -->
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="recalculating" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 max-w-xs mx-4">
          <svg class="w-12 h-12 animate-spin text-teal-400" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <p class="text-sm font-semibold text-gray-900 dark:text-white">Recalculating…</p>
          <p class="text-xs text-gray-500 text-center">Crunching the numbers with your new staking settings</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.help-slide-enter-active,
.help-slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.help-slide-enter-from,
.help-slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.help-slide-enter-to,
.help-slide-leave-from {
  opacity: 1;
  max-height: 500px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'

const betStore = useBetStore()

const stats = computed(() => betStore.summaryStats || {
  num_bets: 0,
  num_wins: 0,
  win_rate: 0,
  total_pl: 0,
  total_staked: 0,
  roi: 0,
  yield_pct: 0,
})

const numStrategies = computed(() => betStore.strategyStats?.length || 0)
</script>

<template>
  <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-sky-500/10 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Tips</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold text-white font-mono">{{ (stats.num_bets || 0).toLocaleString() }}</div>
    </div>

    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Winners</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold text-white font-mono">{{ (stats.num_wins || 0).toLocaleString() }}</div>
    </div>

    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-teal-500/10 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Strike Rate</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold text-white font-mono">{{ (stats.win_rate || 0).toFixed(2) }}%</div>
    </div>

    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg flex items-center justify-center" :class="(stats.total_pl || 0) >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10'">
          <svg class="w-3.5 h-3.5" :class="(stats.total_pl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">P/L (pts)</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold font-mono" :class="(stats.total_pl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">
        {{ (stats.total_pl || 0) >= 0 ? '+' : '' }}{{ (stats.total_pl || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
      </div>
    </div>

    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-sky-500/10 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Invested</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold text-white font-mono">{{ (stats.total_staked || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }}</div>
    </div>

    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg flex items-center justify-center" :class="(stats.roi || 0) >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10'">
          <svg class="w-3.5 h-3.5" :class="(stats.roi || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">ROI</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold font-mono" :class="(stats.roi || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">{{ (stats.roi || 0).toFixed(2) }}%</div>
    </div>

    <div class="stat-card">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
        </div>
        <div class="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Strategies</div>
      </div>
      <div class="mt-2.5 text-2xl font-bold text-white font-mono">{{ numStrategies }}</div>
    </div>
  </div>
</template>

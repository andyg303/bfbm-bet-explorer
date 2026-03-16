<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'
import type { MonthlyPLRow } from '../services/api'

const betStore = useBetStore()

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const grid = computed<MonthlyPLRow[]>(() => betStore.monthlyPLData?.grid || [])
const keyStats = computed(() => betStore.monthlyPLData?.key_stats || null)

function cellClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'text-gray-700'
  if (value > 0) return 'text-emerald-400 font-medium'
  if (value < 0) return 'text-rose-400 font-medium'
  return 'text-gray-500'
}

function fmt(value: number | null | undefined): string {
  if (value === null || value === undefined) return ''
  return value.toFixed(2)
}

function rowTotal(row: any): number {
  let sum = 0
  for (let m = 1; m <= 12; m++) {
    const v = row[String(m)]
    if (v !== null && v !== undefined) sum += v
  }
  return sum
}
</script>

<template>
  <div class="glass-card p-5">
    <h2 class="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
      <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
      Monthly P/L
    </h2>

    <div v-if="grid.length > 0" class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th class="text-left">Year</th>
            <th v-for="(m, i) in months" :key="i" class="text-center">{{ m }}</th>
            <th class="text-center font-bold">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in grid" :key="row.year">
            <td class="font-semibold text-white font-mono">{{ row.year }}</td>
            <td v-for="m in 12" :key="m" class="text-center font-mono" :class="cellClass(row[String(m)])">{{ fmt(row[String(m)]) }}</td>
            <td class="text-center font-semibold font-mono" :class="cellClass(rowTotal(row))">{{ rowTotal(row).toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-center py-8 text-gray-600">No monthly data available</div>

    <!-- Key Statistics -->
    <div v-if="keyStats && grid.length > 0" class="mt-6 border-t border-gray-800/60 pt-6">
      <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Key Statistics</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Total Profit</div>
          <div class="text-lg font-bold font-mono" :class="keyStats.total_profit >= 0 ? 'text-emerald-400' : 'text-rose-400'">{{ keyStats.total_profit.toFixed(2) }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Monthly Avg</div>
          <div class="text-lg font-bold font-mono" :class="keyStats.monthly_average >= 0 ? 'text-emerald-400' : 'text-rose-400'">{{ keyStats.monthly_average.toFixed(2) }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Monthly Low</div>
          <div class="text-lg font-bold font-mono text-rose-400">{{ keyStats.monthly_low.toFixed(2) }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Monthly High</div>
          <div class="text-lg font-bold font-mono text-emerald-400">{{ keyStats.monthly_high.toFixed(2) }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Win Months</div>
          <div class="text-lg font-bold font-mono text-white">{{ keyStats.winning_months }} / {{ keyStats.months_of_data }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Data Months</div>
          <div class="text-lg font-bold font-mono text-white">{{ keyStats.months_of_data }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider">Win Months %</div>
          <div class="text-lg font-bold font-mono" :class="keyStats.winning_months_pct >= 50 ? 'text-emerald-400' : 'text-rose-400'">{{ keyStats.winning_months_pct }}%</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider" title="Biggest drawdown from the starting point of zero">Max Abs DD</div>
          <div class="text-lg font-bold font-mono text-rose-400">{{ keyStats.max_absolute_drawdown.toFixed(2) }}</div>
        </div>
        <div class="stat-card !p-3">
          <div class="text-[11px] text-gray-500 uppercase tracking-wider" title="Biggest drop from a peak to a subsequent trough">Max P/T DD</div>
          <div class="text-lg font-bold font-mono text-rose-400">{{ keyStats.max_peak_trough_drawdown.toFixed(2) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

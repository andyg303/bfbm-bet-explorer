<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'
import type { MonthlyPLRow } from '../services/api'

const betStore = useBetStore()

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const grid = computed<MonthlyPLRow[]>(() => betStore.monthlyPLData?.grid || [])
const keyStats = computed(() => betStore.monthlyPLData?.key_stats || null)

function cellClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'text-gray-300 dark:text-gray-600'
  if (value > 0) return 'text-green-600 dark:text-green-400 font-medium'
  if (value < 0) return 'text-red-600 dark:text-red-400 font-medium'
  return 'text-gray-500 dark:text-gray-400'
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
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Points Profit/Loss Over Time</h2>

    <div v-if="grid.length > 0" class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Year</th>
            <th
              v-for="(m, i) in months"
              :key="i"
              class="px-3 py-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase"
            >
              {{ m }}
            </th>
            <th class="px-3 py-2 text-center text-xs font-bold text-gray-700 dark:text-gray-300 uppercase">Total</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr v-for="row in grid" :key="row.year" class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
            <td class="px-3 py-2 font-semibold text-gray-800 dark:text-gray-200">{{ row.year }}</td>
            <td
              v-for="m in 12"
              :key="m"
              class="px-3 py-2 text-center tabular-nums"
              :class="cellClass(row[String(m)])"
            >
              {{ fmt(row[String(m)]) }}
            </td>
            <td
              class="px-3 py-2 text-center font-semibold tabular-nums"
              :class="cellClass(rowTotal(row))"
            >
              {{ rowTotal(row).toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-center py-8 text-gray-400 dark:text-gray-500">No monthly data available</div>

    <!-- Key Statistics -->
    <div v-if="keyStats && grid.length > 0" class="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 class="text-md font-semibold text-gray-900 dark:text-white mb-4">Key Statistics</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Total Profit</div>
          <div class="text-lg font-bold tabular-nums" :class="keyStats.total_profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
            {{ keyStats.total_profit.toFixed(2) }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Monthly Average</div>
          <div class="text-lg font-bold tabular-nums" :class="keyStats.monthly_average >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
            {{ keyStats.monthly_average.toFixed(2) }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Monthly Low</div>
          <div class="text-lg font-bold tabular-nums text-red-600 dark:text-red-400">
            {{ keyStats.monthly_low.toFixed(2) }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Monthly High</div>
          <div class="text-lg font-bold tabular-nums text-green-600 dark:text-green-400">
            {{ keyStats.monthly_high.toFixed(2) }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Winning Months</div>
          <div class="text-lg font-bold tabular-nums text-gray-900 dark:text-white">
            {{ keyStats.winning_months }} / {{ keyStats.months_of_data }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Months of Data</div>
          <div class="text-lg font-bold tabular-nums text-gray-900 dark:text-white">
            {{ keyStats.months_of_data }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400">Winning Months %</div>
          <div
            class="text-lg font-bold tabular-nums"
            :class="keyStats.winning_months_pct >= 50 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
          >
            {{ keyStats.winning_months_pct }}%
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400" title="Biggest drawdown from the starting point of zero">
            Max Absolute Drawdown
          </div>
          <div class="text-lg font-bold tabular-nums text-red-600 dark:text-red-400">
            {{ keyStats.max_absolute_drawdown.toFixed(2) }}
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div class="text-xs text-gray-500 dark:text-gray-400" title="Biggest drop from a peak to a subsequent trough">
            Max Peak/Trough Drawdown
          </div>
          <div class="text-lg font-bold tabular-nums text-red-600 dark:text-red-400">
            {{ keyStats.max_peak_trough_drawdown.toFixed(2) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { useBetStore } from '../stores/betStore'
import { useDarkMode } from '../composables/useDarkMode'
import { getStrategyComparison, type StrategyComparisonResponse, type StrategyStats } from '../services/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
)

const props = defineProps<{
  strategies: StrategyStats[]
}>()

const emit = defineEmits<{
  close: []
}>()

const betStore = useBetStore()
const { isDark } = useDarkMode()

const loading = ref(false)
const error = ref<string | null>(null)
const comparison = ref<StrategyComparisonResponse | null>(null)
let requestId = 0

const colors = [
  '#14b8a6',
  '#f59e0b',
  '#3b82f6',
  '#f43f5e',
  '#8b5cf6',
  '#22c55e',
  '#eab308',
  '#06b6d4',
]

const strategyNames = computed(() => props.strategies.map((strategy) => strategy.strategy))
const requestKey = computed(() => JSON.stringify({
  filters: betStore.filters,
  staking: betStore.stakingParams,
  strategies: strategyNames.value,
}))

const comparisonItems = computed(() => comparison.value?.strategies || [])
const summaryRows = computed(() => comparisonItems.value.map((item) => item.stats))

const chartLabels = computed(() => {
  const dates = new Set<string>()
  for (const item of comparisonItems.value) {
    for (const point of item.pl_over_time) {
      if (point.date) dates.add(point.date)
    }
  }
  return Array.from(dates).sort()
})

const chartData = computed(() => ({
  labels: chartLabels.value,
  datasets: comparisonItems.value.map((item, index) => {
    const points = new Map(item.pl_over_time.map((point) => [point.date, point.cumulative_pl]))
    let lastValue: number | null = null
    const data = chartLabels.value.map((date) => {
      if (points.has(date)) {
        lastValue = points.get(date) ?? null
      }
      return lastValue
    })

    return {
      label: item.strategy,
      data,
      borderColor: colors[index % colors.length],
      backgroundColor: `${colors[index % colors.length]}1f`,
      tension: 0.25,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 2,
      spanGaps: true,
    }
  }),
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: isDark.value ? '#9ca3af' : '#374151',
        boxWidth: 10,
        boxHeight: 10,
        font: { family: 'JetBrains Mono, monospace', size: 11 },
      },
    },
    title: { display: false },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: '#111827',
      borderColor: '#1f2937',
      borderWidth: 1,
      titleFont: { family: 'DM Sans, sans-serif' },
      bodyFont: { family: 'JetBrains Mono, monospace', size: 11 },
      callbacks: {
        label(context: any) {
          const value = context.parsed.y
          if (value === null || value === undefined) return `${context.dataset.label}:`
          return `${context.dataset.label}: ${formatSignedMoney(value)}`
        },
      },
    },
  },
  scales: {
    x: {
      ticks: {
        color: isDark.value ? '#6b7280' : '#6b7280',
        font: { family: 'JetBrains Mono, monospace', size: 10 },
        maxRotation: 0,
        autoSkip: true,
        maxTicksLimit: 8,
      },
      grid: {
        color: isDark.value ? '#1f2937' : '#e5e7eb',
      },
    },
    y: {
      ticks: {
        color: isDark.value ? '#6b7280' : '#6b7280',
        font: { family: 'JetBrains Mono, monospace', size: 10 },
        callback(value: any) {
          return formatCompactMoney(Number(value))
        },
      },
      grid: {
        color: isDark.value ? '#1f2937' : '#e5e7eb',
      },
    },
  },
}))

const monthlyRows = computed(() => {
  const rows = new Map<string, { month: string; label: string; values: Record<string, number | null> }>()

  for (const item of comparisonItems.value) {
    for (const yearRow of item.monthly_pl.grid) {
      for (let month = 1; month <= 12; month++) {
        const value = yearRow[String(month)]
        if (value === null || value === undefined) continue

        const monthKey = `${yearRow.year}-${String(month).padStart(2, '0')}`
        if (!rows.has(monthKey)) {
          rows.set(monthKey, {
            month: monthKey,
            label: formatMonth(monthKey),
            values: {},
          })
        }
        rows.get(monthKey)!.values[item.strategy] = value
      }
    }
  }

  return Array.from(rows.values()).sort((a, b) => a.month.localeCompare(b.month))
})

watch(requestKey, () => {
  loadComparison()
}, { immediate: true })

async function loadComparison() {
  if (strategyNames.value.length < 2) {
    comparison.value = null
    return
  }

  const currentRequest = ++requestId
  loading.value = true
  error.value = null

  try {
    const filtersWithStaking = {
      ...betStore.filters,
      ...betStore.stakingParams,
      strategies: strategyNames.value,
    }
    const data = await getStrategyComparison(filtersWithStaking)
    if (currentRequest === requestId) {
      comparison.value = data
    }
  } catch (err: any) {
    if (currentRequest === requestId) {
      error.value = err?.response?.data?.detail || 'Could not load strategy comparison.'
      comparison.value = null
    }
  } finally {
    if (currentRequest === requestId) {
      loading.value = false
    }
  }
}

function formatMonth(monthKey: string) {
  const [year, month] = monthKey.split('-')
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
}

function formatCompactMoney(value: number) {
  const abs = Math.abs(value)
  if (abs >= 1000) return `${value < 0 ? '-' : ''}£${(abs / 1000).toFixed(1)}k`
  return `${value < 0 ? '-' : ''}£${abs.toFixed(0)}`
}

function formatSignedMoney(value: number | null | undefined) {
  if (value === null || value === undefined) return ''
  const abs = Math.abs(value)
  return `${value >= 0 ? '+' : '-'}£${abs.toFixed(2)}`
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return ''
  return `${value.toFixed(2)}%`
}

function valueClass(value: number | null | undefined) {
  if (value === null || value === undefined) return 'text-gray-400 dark:text-gray-600'
  if (value > 0) return 'text-emerald-600 dark:text-emerald-400 font-medium'
  if (value < 0) return 'text-rose-600 dark:text-rose-400 font-medium'
  return 'text-gray-500 dark:text-gray-400'
}
</script>

<template>
  <section class="glass-card p-5 space-y-5">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
          <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
          Strategy Comparison
        </h3>
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          {{ strategyNames.length }} selected strategies
        </p>
      </div>
      <div class="flex items-center justify-end">
        <button
          @click="emit('close')"
          class="inline-flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-teal-500 dark:hover:text-teal-400 transition-colors"
        >
          <svg class="w-3.5 h-3.5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
          Hide Strategy Comparison
        </button>
      </div>
    </div>

    <div v-if="loading" class="h-80 flex items-center justify-center text-sm text-gray-500">
      Loading comparison...
    </div>

    <div v-else-if="error" class="p-3 rounded-lg text-sm font-medium bg-rose-500/10 border border-rose-500/20 text-rose-500">
      {{ error }}
    </div>

    <div v-else-if="comparisonItems.length > 0" class="space-y-6">
      <div>
        <div class="h-80">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th class="text-left">System</th>
              <th class="text-center">Avg Odds</th>
              <th class="text-center">Selections</th>
              <th class="text-center">Win Rate</th>
              <th class="text-center">P/L</th>
              <th class="text-center">ROI</th>
              <th class="text-center">Reverse ROI</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in summaryRows" :key="row.strategy">
              <td class="strategy-cell font-medium text-gray-900 dark:text-white">{{ row.strategy }}</td>
              <td class="text-center font-mono">{{ row.avg_odds.toFixed(2) }}</td>
              <td class="text-center font-mono">{{ row.num_bets.toLocaleString() }}</td>
              <td class="text-center font-mono">{{ formatPercent(row.win_rate) }}</td>
              <td class="text-center font-mono" :class="valueClass(row.total_pl)">{{ formatSignedMoney(row.total_pl) }}</td>
              <td class="text-center font-mono" :class="valueClass(row.roi)">{{ formatPercent(row.roi) }}</td>
              <td class="text-center font-mono" :class="valueClass(row.yield_pct)">{{ formatPercent(row.yield_pct) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th class="text-left">Month</th>
              <th v-for="item in comparisonItems" :key="item.strategy" class="text-center">
                {{ item.strategy }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in monthlyRows" :key="row.month">
              <td class="font-semibold text-gray-900 dark:text-white font-mono">{{ row.label }}</td>
              <td
                v-for="item in comparisonItems"
                :key="item.strategy"
                class="text-center font-mono"
                :class="valueClass(row.values[item.strategy])"
              >
                {{ formatSignedMoney(row.values[item.strategy]) }}
              </td>
            </tr>
            <tr v-if="monthlyRows.length === 0">
              <td :colspan="comparisonItems.length + 1" class="!py-8 text-center text-sm text-gray-500">No monthly data available</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

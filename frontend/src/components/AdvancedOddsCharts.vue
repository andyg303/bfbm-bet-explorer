<script setup lang="ts">
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useBetStore } from '../stores/betStore'
import { useDarkMode } from '../composables/useDarkMode'
import { Chart, registerables, LogarithmicScale } from 'chart.js'

Chart.register(...registerables, LogarithmicScale)

const betStore = useBetStore()
const { isDark } = useDarkMode()

const showAdvanced = ref(false)
const isLoading = ref(false)
const profitCanvas = ref<HTMLCanvasElement | null>(null)
const roiCanvas = ref<HTMLCanvasElement | null>(null)
let profitChart: Chart | null = null
let roiChart: Chart | null = null

const curveData = computed(() => betStore.oddsCurveData || [])

async function toggleAdvanced() {
  if (showAdvanced.value) {
    showAdvanced.value = false
    return
  }
  showAdvanced.value = true
  isLoading.value = true
  try {
    await betStore.loadOddsCurveData()
  } finally {
    isLoading.value = false
  }
  await nextTick()
  createCharts()
}

function getColors() {
  const textColor = isDark.value ? '#6b7280' : '#374151'
  const gridColor = isDark.value ? '#1f2937' : '#e5e7eb'
  return { textColor, gridColor }
}

function createProfitChart() {
  if (!profitCanvas.value || curveData.value.length === 0) return
  if (profitChart) profitChart.destroy()

  const { textColor, gridColor } = getColors()
  const data = curveData.value

  profitChart = new Chart(profitCanvas.value, {
    type: 'line',
    data: {
      labels: data.map(d => d.odds),
      datasets: [
        {
          label: 'Cumulative P&L',
          data: data.map(d => d.cum_pl),
          borderColor: isDark.value ? '#d1d5db' : '#374151',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0,
        },
        {
          label: 'Cumulative EV',
          data: data.map(d => d.cum_ev),
          borderColor: 'rgb(20, 184, 166)',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: textColor, font: { size: 11 } },
        },
        title: {
          display: true,
          text: 'Profit Curve by Odds',
          color: textColor,
          font: { size: 14, weight: 'bold', family: 'DM Sans, sans-serif' },
        },
        subtitle: {
          display: true,
          text: 'Cumulative P&L and EV walking from low to high odds — shows exactly where your edge is strongest',
          color: isDark.value ? '#9ca3af' : '#6b7280',
          font: { size: 11, family: 'DM Sans, sans-serif' },
          padding: { bottom: 10 },
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: '#1f2937',
          borderWidth: 1,
          titleFont: { family: 'DM Sans, sans-serif' },
          bodyFont: { family: 'JetBrains Mono, monospace', size: 11 },
          callbacks: {
            title: (items) => `Odds: ${items[0]?.label}`,
            label: (ctx) => `${ctx.dataset.label}: £${(ctx.parsed.y ?? 0).toFixed(2)}`,
          },
        },
      },
      scales: {
        x: {
          type: 'logarithmic',
          title: { display: true, text: 'Odds', color: textColor },
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            font: { size: 10 },
            callback: function (value) {
              const v = Number(value)
              if ([1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 400].includes(v)) return v.toFixed(1)
              return ''
            },
            autoSkip: false,
            maxRotation: 0,
          },
          min: 1,
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            callback: (value) => '£' + value,
          },
          title: { display: true, text: 'Cumulative £', color: textColor },
        },
      },
    },
  })
}

function createRoiChart() {
  if (!roiCanvas.value || curveData.value.length === 0) return
  if (roiChart) roiChart.destroy()

  const { textColor, gridColor } = getColors()
  const data = curveData.value

  roiChart = new Chart(roiCanvas.value, {
    type: 'line',
    data: {
      labels: data.map(d => d.odds),
      datasets: [
        {
          label: 'Cumulative ROI % (P&L)',
          data: data.map(d => d.roi_pl),
          borderColor: isDark.value ? '#d1d5db' : '#374151',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0,
        },
        {
          label: 'Cumulative ROI % (EV)',
          data: data.map(d => d.roi_ev),
          borderColor: 'rgb(20, 184, 166)',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: textColor, font: { size: 11 } },
        },
        title: {
          display: true,
          text: 'ROI Curve by Odds',
          color: textColor,
          font: { size: 14, weight: 'bold', family: 'DM Sans, sans-serif' },
        },
        subtitle: {
          display: true,
          text: 'Cumulative ROI% walking from low to high odds (cumulative P&L ÷ cumulative stake). Shows how ROI evolves as you include longer-priced bets.',
          color: isDark.value ? '#9ca3af' : '#6b7280',
          font: { size: 11, family: 'DM Sans, sans-serif' },
          padding: { bottom: 10 },
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: '#1f2937',
          borderWidth: 1,
          titleFont: { family: 'DM Sans, sans-serif' },
          bodyFont: { family: 'JetBrains Mono, monospace', size: 11 },
          callbacks: {
            title: (items) => `Odds: ${items[0]?.label}`,
            label: (ctx) => `${ctx.dataset.label}: ${(ctx.parsed.y ?? 0).toFixed(2)}%`,
          },
        },
      },
      scales: {
        x: {
          type: 'logarithmic',
          title: { display: true, text: 'Odds', color: textColor },
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            font: { size: 10 },
            callback: function (value) {
              const v = Number(value)
              if ([1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 400].includes(v)) return v.toFixed(1)
              return ''
            },
            autoSkip: false,
            maxRotation: 0,
          },
          min: 1,
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            callback: (value) => value + '%',
          },
          title: { display: true, text: 'Cumulative ROI %', color: textColor },
        },
      },
    },
  })
}

function createCharts() {
  createProfitChart()
  createRoiChart()
}

watch([curveData, isDark], async () => {
  if (showAdvanced.value && curveData.value.length > 0) {
    await nextTick()
    createCharts()
  }
}, { deep: true })

onBeforeUnmount(() => {
  profitChart?.destroy()
  roiChart?.destroy()
})
</script>

<template>
  <div class="glass-card p-5">
    <div class="flex items-center justify-between mb-4">
      <button
        @click="toggleAdvanced"
        class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        :class="showAdvanced
          ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30 hover:bg-teal-500/20'
          : 'bg-gray-500/10 text-gray-400 border border-gray-500/30 hover:bg-gray-500/20 dark:text-gray-300'"
      >
        <svg v-if="!isLoading" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform" :class="{ 'rotate-180': showAdvanced }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
        <svg v-else class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        {{ showAdvanced ? 'Hide' : 'Show' }} Advanced Odds Charts
      </button>
    </div>

    <div v-if="showAdvanced">
      <div v-if="isLoading" class="flex flex-col items-center justify-center h-64 gap-3">
        <svg class="animate-spin h-8 w-8 text-teal-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <span class="text-sm text-gray-400">Loading advanced charts…</span>
      </div>

      <div v-else-if="curveData.length > 0" class="space-y-6">
        <div style="height: 400px;">
          <canvas ref="profitCanvas"></canvas>
        </div>
        <div style="height: 400px;">
          <canvas ref="roiCanvas"></canvas>
        </div>
      </div>

      <div v-else class="flex items-center justify-center h-32 text-gray-500 text-sm">
        No data available for these filters
      </div>
    </div>
  </div>
</template>

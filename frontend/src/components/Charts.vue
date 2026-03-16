<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useBetStore } from '../stores/betStore'
import { useDarkMode } from '../composables/useDarkMode'
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
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const betStore = useBetStore()
const { isDark } = useDarkMode()

const plData = computed(() => betStore.plOverTime)

const chartData = computed(() => {
  if (!plData.value || plData.value.length === 0) {
    return {
      labels: [],
      datasets: []
    }
  }

  // Determine line colour based on final cumulative P/L (green if profitable, red if not)
  const lastCumPL = plData.value[plData.value.length - 1]?.cumulative_pl ?? 0
  const lineColor = lastCumPL >= 0 ? 'rgb(16, 185, 129)' : 'rgb(244, 63, 94)'
  const fillColor = lastCumPL >= 0 ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)'

  return {
    labels: plData.value.map(d => d.date),
    datasets: [
      {
        label: 'Cumulative P/L',
        data: plData.value.map(d => d.cumulative_pl),
        borderColor: lineColor,
        backgroundColor: fillColor,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2
      }
    ]
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: isDark.value ? '#9ca3af' : '#374151',
        font: { family: 'JetBrains Mono, monospace', size: 11 }
      }
    },
    title: {
      display: false
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: '#111827',
      borderColor: '#1f2937',
      borderWidth: 1,
      titleFont: { family: 'DM Sans, sans-serif' },
      bodyFont: { family: 'JetBrains Mono, monospace', size: 11 }
    }
  },
  scales: {
    x: {
      ticks: {
        color: isDark.value ? '#4b5563' : '#6b7280',
        font: { family: 'JetBrains Mono, monospace', size: 10 }
      },
      grid: {
        color: isDark.value ? '#1f2937' : '#e5e7eb'
      }
    },
    y: {
      beginAtZero: true,
      ticks: {
        color: isDark.value ? '#4b5563' : '#6b7280',
        font: { family: 'JetBrains Mono, monospace', size: 10 },
        callback: function(value: any) {
          return '£' + value.toLocaleString()
        }
      },
      grid: {
        color: isDark.value ? '#1f2937' : '#e5e7eb'
      }
    }
  }
}))
</script>

<template>
  <div class="glass-card p-5">
    <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2 mb-4">
      <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
      Profit/Loss Over Time
    </h2>
    
    <div v-if="plData && plData.length > 0" class="h-96">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    
    <div v-else class="h-96 flex items-center justify-center text-gray-600">
      No data available for chart
    </div>
  </div>
</template>

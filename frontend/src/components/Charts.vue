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
  const lineColor = lastCumPL >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
  const fillColor = lastCumPL >= 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)'

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
        color: isDark.value ? '#e5e7eb' : '#374151'
      }
    },
    title: {
      display: false
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
    }
  },
  scales: {
    x: {
      ticks: {
        color: isDark.value ? '#9ca3af' : '#6b7280'
      },
      grid: {
        color: isDark.value ? '#4b5563' : '#e5e7eb'
      }
    },
    y: {
      beginAtZero: true,
      ticks: {
        color: isDark.value ? '#9ca3af' : '#6b7280',
        callback: function(value: any) {
          return '£' + value.toLocaleString()
        }
      },
      grid: {
        color: isDark.value ? '#4b5563' : '#e5e7eb'
      }
    }
  }
}))
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Profit/Loss Over Time</h2>
    
    <div v-if="plData && plData.length > 0" class="h-96">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    
    <div v-else class="h-96 flex items-center justify-center text-gray-500 dark:text-gray-400">
      No data available for chart
    </div>
  </div>
</template>

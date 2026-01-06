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

  return {
    labels: plData.value.map(d => d.date),
    datasets: [
      {
        label: 'Cumulative P/L',
        data: plData.value.map(d => d.cumulative_pl),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Daily P/L',
        data: plData.value.map(d => d.daily_pl),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: false,
        tension: 0.4
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

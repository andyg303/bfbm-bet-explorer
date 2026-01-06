<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useBetStore } from '../stores/betStore'
import { useDarkMode } from '../composables/useDarkMode'
import { Chart, registerables } from 'chart.js'
import type { OddsBandProfit } from '../services/api'

Chart.register(...registerables)

const betStore = useBetStore()
const { isDark } = useDarkMode()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const oddsBandsData = computed(() => betStore.oddsBandsData || [])

const chartData = computed(() => {
  const data = oddsBandsData.value
  
  return {
    labels: data.map(d => d.band),
    datasets: [
      {
        label: 'Profit/Loss (£)',
        data: data.map(d => d.total_pl),
        backgroundColor: data.map(d => d.total_pl >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'),
        borderColor: data.map(d => d.total_pl >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'),
        borderWidth: 1,
        yAxisID: 'y'
      },
      {
        label: 'Number of Bets',
        data: data.map(d => d.num_bets),
        type: 'line' as const,
        borderColor: isDark.value ? 'rgb(147, 197, 253)' : 'rgb(59, 130, 246)',
        backgroundColor: isDark.value ? 'rgba(147, 197, 253, 0.1)' : 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        yAxisID: 'y1',
        tension: 0.3
      }
    ]
  }
})

function createChart() {
  if (!chartCanvas.value) return
  
  if (chartInstance) {
    chartInstance.destroy()
  }

  const textColor = isDark.value ? '#e5e7eb' : '#374151'
  const gridColor = isDark.value ? '#4b5563' : '#e5e7eb'

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: chartData.value,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: textColor,
            font: {
              size: 12
            }
          }
        },
        title: {
          display: true,
          text: 'Profit/Loss & Bet Volume by Odds Bands',
          color: textColor,
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              if (context.datasetIndex === 0) {
                return `${label}: £${value.toFixed(2)}`
              } else {
                return `${label}: ${value}`
              }
            },
            afterLabel: function(context) {
              const index = context.dataIndex
              const data = oddsBandsData.value[index]
              return `ROI: ${data.roi.toFixed(2)}%\nStaked: £${data.total_staked.toFixed(2)}`
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor,
            callback: function(value) {
              return '£' + value
            }
          },
          title: {
            display: true,
            text: 'Profit/Loss (£)',
            color: textColor
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: {
            drawOnChartArea: false,
          },
          ticks: {
            color: textColor,
            callback: function(value) {
              return value
            }
          },
          title: {
            display: true,
            text: 'Number of Bets',
            color: textColor
          }
        }
      }
    }
  })
}

watch([oddsBandsData, isDark], async () => {
  if (oddsBandsData.value.length > 0) {
    await nextTick()
    createChart()
  }
}, { deep: true })

onMounted(async () => {
  // Wait for data to load if not already available
  if (oddsBandsData.value.length > 0) {
    await nextTick()
    createChart()
  }
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <div v-if="oddsBandsData.length > 0" style="height: 400px;">
      <canvas ref="chartCanvas"></canvas>
    </div>
    <div v-else class="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
      No data available
    </div>
  </div>
</template>

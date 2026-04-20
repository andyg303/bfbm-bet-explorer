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
const roiCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
let roiChartInstance: Chart | null = null

const oddsBandsData = computed(() => betStore.oddsBandsData || [])

const chartData = computed(() => {
  const data = oddsBandsData.value
  
  return {
    labels: data.map(d => d.band),
    datasets: [
      {
        label: 'Profit/Loss (£)',
        data: data.map(d => d.total_pl),
        backgroundColor: data.map(d => d.total_pl >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(244, 63, 94, 0.7)'),
        borderColor: data.map(d => d.total_pl >= 0 ? 'rgb(16, 185, 129)' : 'rgb(244, 63, 94)'),
        borderWidth: 1,
        yAxisID: 'y'
      },
      {
        label: 'Number of Bets',
        data: data.map(d => d.num_bets),
        type: 'line' as const,
        borderColor: isDark.value ? 'rgb(20, 184, 166)' : 'rgb(59, 130, 246)',
        backgroundColor: isDark.value ? 'rgba(20, 184, 166, 0.1)' : 'rgba(59, 130, 246, 0.1)',
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

  const textColor = isDark.value ? '#6b7280' : '#374151'
  const gridColor = isDark.value ? '#1f2937' : '#e5e7eb'

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
            size: 14,
            weight: 'bold',
            family: 'DM Sans, sans-serif'
          }
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: '#1f2937',
          borderWidth: 1,
          titleFont: { family: 'DM Sans, sans-serif' },
          bodyFont: { family: 'JetBrains Mono, monospace', size: 11 },
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              if (value === null || value === undefined) return label
              if (context.datasetIndex === 0) {
                return `${label}: £${value.toFixed(2)}`
              } else {
                return `${label}: ${value}`
              }
            },
            afterLabel: function(context) {
              const index = context.dataIndex
              const data = oddsBandsData.value[index]
              if (!data) return ''
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

function createRoiChart() {
  if (!roiCanvas.value) return
  if (roiChartInstance) roiChartInstance.destroy()

  const textColor = isDark.value ? '#6b7280' : '#374151'
  const gridColor = isDark.value ? '#1f2937' : '#e5e7eb'
  const data = oddsBandsData.value

  roiChartInstance = new Chart(roiCanvas.value, {
    type: 'bar',
    data: {
      labels: data.map(d => d.band),
      datasets: [
        {
          label: 'ROI %',
          data: data.map(d => d.roi),
          backgroundColor: data.map(d => d.roi >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(244, 63, 94, 0.7)'),
          borderColor: data.map(d => d.roi >= 0 ? 'rgb(16, 185, 129)' : 'rgb(244, 63, 94)'),
          borderWidth: 1,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: 'ROI % by Odds Bands',
          color: textColor,
          font: { size: 14, weight: 'bold', family: 'DM Sans, sans-serif' }
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: '#1f2937',
          borderWidth: 1,
          titleFont: { family: 'DM Sans, sans-serif' },
          bodyFont: { family: 'JetBrains Mono, monospace', size: 11 },
          callbacks: {
            label: function(context) {
              const value = context.parsed.y
              if (value === null || value === undefined) return ''
              return `ROI: ${value.toFixed(2)}%`
            },
            afterLabel: function(context) {
              const d = oddsBandsData.value[context.dataIndex]
              if (!d) return ''
              return `P&L: £${d.total_pl.toFixed(2)}\nStaked: £${d.total_staked.toFixed(2)}\nBets: ${d.num_bets}`
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor }
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            callback: function(value) { return value + '%' }
          },
          title: { display: true, text: 'ROI %', color: textColor }
        }
      }
    }
  })
}

function createAll() {
  createChart()
  createRoiChart()
}

watch([oddsBandsData, isDark], async () => {
  if (oddsBandsData.value.length > 0) {
    await nextTick()
    createAll()
  }
}, { deep: true })

onMounted(async () => {
  if (oddsBandsData.value.length > 0) {
    await nextTick()
    createAll()
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="glass-card p-5">
      <div v-if="oddsBandsData.length > 0" style="height: 400px;">
        <canvas ref="chartCanvas"></canvas>
      </div>
      <div v-else class="flex items-center justify-center h-64 text-gray-600">
        No data available
      </div>
    </div>
    <div class="glass-card p-5">
      <div v-if="oddsBandsData.length > 0" style="height: 350px;">
        <canvas ref="roiCanvas"></canvas>
      </div>
      <div v-else class="flex items-center justify-center h-64 text-gray-600">
        No data available
      </div>
    </div>
  </div>
</template>

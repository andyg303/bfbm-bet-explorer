<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBetStore } from '../stores/betStore'
import type { Bet } from '../services/api'

const betStore = useBetStore()
const currentPage = ref(0)
const pageSize = ref(100)
const pageSizeOptions = [100, 250, 500]

type SortableKey = 'settled_date' | 'description' | 'selection' | 'bet_type' | 'matched_amount' | 'avg_price_matched' | 'bsp' | 'bsp_diff_absolute' | 'bsp_diff_percentage' | 'bsp_diff_probability' | 'lay_liability' | 'status' | 'profit_loss' | 'strategy' | 'event' | 'competition' | 'market_type'
const sortKey = ref<SortableKey>('settled_date')
const sortDirection = ref<'asc' | 'desc'>('desc')

const isCustomStaking = computed(() => betStore.stakingParams.staking_type !== 'default')

const bets = computed(() => {
  const data = betStore.bets || []
  if (!data.length) return data
  
  const sorted = [...data].sort((a, b) => {
    let aVal = a[sortKey.value]
    let bVal = b[sortKey.value]
    
    // Use recalculated values when custom staking is applied
    if (isCustomStaking.value) {
      if (sortKey.value === 'matched_amount' && a.recalculated_stake !== undefined) {
        aVal = a.recalculated_stake
      }
      if (sortKey.value === 'matched_amount' && b.recalculated_stake !== undefined) {
        bVal = b.recalculated_stake
      }
      if (sortKey.value === 'profit_loss' && a.recalculated_pl !== undefined) {
        aVal = a.recalculated_pl
      }
      if (sortKey.value === 'profit_loss' && b.recalculated_pl !== undefined) {
        bVal = b.recalculated_pl
      }
      if (sortKey.value === 'lay_liability' && a.recalculated_liability !== undefined) {
        aVal = a.recalculated_liability
      }
      if (sortKey.value === 'lay_liability' && b.recalculated_liability !== undefined) {
        bVal = b.recalculated_liability
      }
    }
    
    // Handle null/undefined
    if (aVal == null && bVal == null) return 0
    if (aVal == null) return 1
    if (bVal == null) return -1
    
    // Handle string comparison
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection.value === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }
    
    // Handle numeric comparison
    const aNum = Number(aVal) || 0
    const bNum = Number(bVal) || 0
    return sortDirection.value === 'asc' ? aNum - bNum : bNum - aNum
  })
  
  return sorted
})

const totalBets = computed(() => betStore.totalBets)
const totalPages = computed(() => Math.ceil(totalBets.value / pageSize.value))

function sort(key: SortableKey) {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'desc'
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++
    betStore.loadBets(currentPage.value * pageSize.value, pageSize.value)
  }
}

function prevPage() {
  if (currentPage.value > 0) {
    currentPage.value--
    betStore.loadBets(currentPage.value * pageSize.value, pageSize.value)
  }
}

function formatDate(date: string | null) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

function changePageSize(newSize: number) {
  pageSize.value = newSize
  currentPage.value = 0
  betStore.loadBets(0, newSize)
}

async function generateCSVContent() {
  // Fetch all bets with current filters
  const filtersWithStaking = { ...betStore.filters, ...betStore.stakingParams }
  const response = await fetch('http://localhost:8000/bets?skip=0&limit=999999', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filtersWithStaking)
  })
  const data = await response.json()
  const allBets = data.bets
  
  // Create CSV content
  const headers = [
    'Date', 'Strategy', 'Event', 'Selection', 'Type', 'Stake', 'Odds', 'BSP',
    'BSP Diff', 'BSP %', 'BSP Prob', 'Liability', 'P/L', 'Market', 'Competition'
  ]
  
  if (isCustomStaking.value) {
    headers.splice(5, 0, 'Recalc Stake')
    headers.splice(12, 0, 'Recalc Liability')
    headers.splice(14, 0, 'Recalc P/L')
  }
  
  const csvRows = [headers.join(',')]
  
  for (const bet of allBets) {
    const row = [
      formatDate(bet.settled_date),
      `"${bet.strategy || ''}"`,
      `"${bet.event || ''}"`,
      `"${bet.selection || ''}"`,
      bet.bet_type || '',
      bet.matched_amount?.toFixed(2) || '',
      bet.avg_price_matched?.toFixed(2) || '',
      bet.bsp?.toFixed(2) || '',
      bet.bsp_diff_absolute?.toFixed(3) || '',
      bet.bsp_diff_percentage?.toFixed(2) || '',
      bet.bsp_diff_probability?.toFixed(2) || '',
      bet.lay_liability?.toFixed(2) || '',
      bet.profit_loss?.toFixed(2) || '',
      `"${bet.market_type || ''}"`,
      `"${bet.competition || ''}"`
    ]
    
    if (isCustomStaking.value && bet.recalculated_stake) {
      row.splice(5, 0, bet.recalculated_stake.toFixed(2))
      row.splice(12, 0, bet.recalculated_liability?.toFixed(2) || '')
      row.splice(14, 0, bet.recalculated_pl?.toFixed(2) || '')
    }
    
    csvRows.push(row.join(','))
  }
  
  return csvRows.join('\n')
}

async function copyToClipboard() {
  const csvContent = await generateCSVContent()
  await navigator.clipboard.writeText(csvContent)
  alert('CSV data copied to clipboard!')
}

async function exportToCSV() {
  const csvContent = await generateCSVContent()
  
  // Download CSV
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `bets_export_${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow">
    <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Bets</h2>
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-700 dark:text-gray-300">Show:</label>
            <select v-model.number="pageSize" @change="changePageSize(pageSize)" class="border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
            </select>
            <span class="text-sm text-gray-700 dark:text-gray-300">per page</span>
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <button @click="copyToClipboard" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md">
            Copy All to Clipboard
          </button>
          <button @click="exportToCSV" class="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md">
            Export All to CSV
          </button>
          <div class="text-sm text-gray-500 dark:text-gray-400">{{ totalBets.toLocaleString() }} total bets</div>
          <button @click="prevPage" :disabled="currentPage === 0" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed">
            Previous
          </button>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            Page {{ currentPage + 1 }} of {{ totalPages }}
          </span>
          <button @click="nextPage" :disabled="currentPage >= totalPages - 1" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed">
            Next
          </button>
        </div>
      </div>
    </div>
    
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th @click="sort('settled_date')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Date <span v-if="sortKey === 'settled_date'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('strategy')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Strategy <span v-if="sortKey === 'strategy'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('event')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Event <span v-if="sortKey === 'event'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('selection')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Selection <span v-if="sortKey === 'selection'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('bet_type')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Type <span v-if="sortKey === 'bet_type'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('matched_amount')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Stake <span v-if="sortKey === 'matched_amount'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_price_matched')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Odds <span v-if="sortKey === 'avg_price_matched'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('bsp')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              BSP <span v-if="sortKey === 'bsp'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('bsp_diff_absolute')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              BSP Diff <span v-if="sortKey === 'bsp_diff_absolute'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('bsp_diff_percentage')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              BSP % <span v-if="sortKey === 'bsp_diff_percentage'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('bsp_diff_probability')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              BSP Prob <span v-if="sortKey === 'bsp_diff_probability'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('lay_liability')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Liability <span v-if="sortKey === 'lay_liability'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('profit_loss')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              P/L <span v-if="sortKey === 'profit_loss'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('market_type')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Market <span v-if="sortKey === 'market_type'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('competition')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 whitespace-nowrap">
              Competition <span v-if="sortKey === 'competition'">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="bet in bets" :key="bet.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ formatDate(bet.settled_date) }}</td>
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-white max-w-xs truncate">{{ bet.strategy }}</td>
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-white max-w-xs truncate">{{ bet.event }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">{{ bet.selection }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm">
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="bet.bet_type === 'BACK' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' : 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200'">
                {{ bet.bet_type }}
              </span>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              <div v-if="isCustomStaking && bet.recalculated_stake">
                <div class="font-semibold text-blue-600 dark:text-blue-400">£{{ bet.recalculated_stake.toFixed(2) }}</div>
                <div class="text-xs text-gray-400 dark:text-gray-500 line-through">£{{ bet.matched_amount?.toFixed(2) }}</div>
              </div>
              <div v-else>£{{ bet.matched_amount?.toFixed(2) }}</div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ bet.avg_price_matched?.toFixed(2) }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ bet.bsp?.toFixed(2) || '-' }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm" :class="(bet.bsp_diff_absolute || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ bet.bsp_diff_absolute ? ((bet.bsp_diff_absolute > 0 ? '+' : '') + bet.bsp_diff_absolute.toFixed(3)) : '-' }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm" :class="(bet.bsp_diff_percentage || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ bet.bsp_diff_percentage ? ((bet.bsp_diff_percentage > 0 ? '+' : '') + bet.bsp_diff_percentage.toFixed(2) + '%') : '-' }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm" :class="(bet.bsp_diff_probability || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ bet.bsp_diff_probability ? ((bet.bsp_diff_probability > 0 ? '+' : '') + bet.bsp_diff_probability.toFixed(2) + '%') : '-' }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              <div v-if="isCustomStaking && bet.recalculated_liability !== undefined">
                <div class="font-semibold text-blue-600 dark:text-blue-400">£{{ bet.recalculated_liability.toFixed(2) }}</div>
                <div class="text-xs text-gray-400 dark:text-gray-500 line-through">{{ bet.lay_liability ? '£' + bet.lay_liability.toFixed(2) : '-' }}</div>
              </div>
              <div v-else>{{ bet.lay_liability ? '£' + bet.lay_liability.toFixed(2) : '-' }}</div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
              <div v-if="isCustomStaking && bet.recalculated_pl !== undefined">
                <div class="font-semibold" :class="bet.recalculated_pl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                  £{{ bet.recalculated_pl.toFixed(2) }}
                </div>
                <div class="text-xs text-gray-400 dark:text-gray-500 line-through">£{{ bet.profit_loss?.toFixed(2) }}</div>
              </div>
              <div v-else :class="(bet.profit_loss || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                £{{ bet.profit_loss?.toFixed(2) }}
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ bet.market_type }}</td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">{{ bet.competition }}</td>
          </tr>
          <tr v-if="!bets || bets.length === 0">
            <td colspan="15" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">No bets found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-center items-center">
      <span class="text-sm text-gray-500 dark:text-gray-400">
        Showing {{ bets.length }} of {{ totalBets.toLocaleString() }} bets
      </span>
    </div>
  </div>
</template>

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

const isDedup = computed(() => isCustomStaking.value && betStore.stakingParams.deduplicate)

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

function formatTime(description: string | null | undefined) {
  if (!description) return '-'
  // Match HH:MM at the start of the description (e.g. "15:00 Southend...")
  const match = description.match(/^(\d{1,2}:\d{2})/)
  return match ? match[1] : '-'
}

function formatEventName(description: string | null | undefined) {
  if (!description) return '-'
  // Strip leading time (e.g. "15:00 Southend Dogs" → "Southend Dogs")
  return description.replace(/^\d{1,2}:\d{2}\s*/, '') || description
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
    'Date', 'Time', 'Event', 'Selection', 'Sport', 'Strategy', 'Type', 'Stake', 'Odds', 'BSP',
    'BSP Diff', 'BSP %', 'BSP Prob', 'Liability', 'P/L', 'Market', 'Competition'
  ]
  
  if (isCustomStaking.value) {
    headers.splice(7, 0, 'Recalc Stake')
    headers.splice(14, 0, 'Recalc Liability')
    headers.splice(16, 0, 'Recalc P/L')
  }
  
  if (isDedup.value) {
    headers.push('# Strats', 'Strategies Triggered')
  }
  
  const csvRows = [headers.join(',')]
  
  for (const bet of allBets) {
    const row = [
      formatDate(bet.settled_date),
      formatTime(bet.description),
      `"${formatEventName(bet.description)}"`,
      `"${bet.selection || ''}"`,
      `"${bet.event || ''}"`,
      `"${bet.strategy || ''}"`,
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
      row.splice(7, 0, bet.recalculated_stake.toFixed(2))
      row.splice(14, 0, bet.recalculated_liability?.toFixed(2) || '')
      row.splice(16, 0, bet.recalculated_pl?.toFixed(2) || '')
    }
    
    if (isDedup.value) {
      row.push(String(bet.strategy_count || 1))
      row.push(`"${(bet.strategies_triggered || []).join(', ')}"`)
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

const deletingId = ref<number | null>(null)

async function handleDelete(bet: any) {
  if (!confirm(`Delete this bet (${bet.selection} @ ${bet.avg_price_matched?.toFixed(2)})? It will be hidden from all views but kept in the database.`)) return
  deletingId.value = bet.id
  try {
    await betStore.deleteBet(bet.id)
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <div class="glass-card overflow-hidden">
    <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800/60">
      <div class="flex flex-wrap justify-between items-center gap-3">
        <div class="flex items-center gap-4">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
            Bets
          </h2>
          <div class="flex items-center gap-2">
            <label class="text-xs text-gray-500">Show:</label>
            <select v-model.number="pageSize" @change="changePageSize(pageSize)" class="input-field !w-auto !py-1 !px-2 text-xs">
              <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
            </select>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button @click="copyToClipboard" class="px-3 py-1.5 text-xs font-medium text-teal-400 bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/20 rounded-lg transition-colors">Copy All</button>
          <button @click="exportToCSV" class="px-3 py-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-lg transition-colors">Export CSV</button>
          <span class="text-xs text-gray-500 font-mono">{{ totalBets.toLocaleString() }} bets</span>
          <button @click="prevPage" :disabled="currentPage === 0" class="px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-800/50 border border-gray-300 dark:border-gray-700/50 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed">Prev</button>
          <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">{{ currentPage + 1 }}/{{ totalPages }}</span>
          <button @click="nextPage" :disabled="currentPage >= totalPages - 1" class="px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-800/50 border border-gray-300 dark:border-gray-700/50 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed">Next</button>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="sort('settled_date')" class="cursor-pointer hover:text-teal-400 transition-colors">Date <span v-if="sortKey === 'settled_date'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th class="whitespace-nowrap">Time</th>
            <th @click="sort('description')" class="cursor-pointer hover:text-teal-400 transition-colors">Event <span v-if="sortKey === 'description'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('selection')" class="cursor-pointer hover:text-teal-400 transition-colors">Selection <span v-if="sortKey === 'selection'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('event')" class="cursor-pointer hover:text-teal-400 transition-colors">Sport <span v-if="sortKey === 'event'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('strategy')" class="cursor-pointer hover:text-teal-400 transition-colors">Strategy <span v-if="sortKey === 'strategy'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th v-if="isDedup" class="text-center whitespace-nowrap text-teal-400"># Strats</th>
            <th @click="sort('bet_type')" class="cursor-pointer hover:text-teal-400 transition-colors">Type <span v-if="sortKey === 'bet_type'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('matched_amount')" class="cursor-pointer hover:text-teal-400 transition-colors">Stake <span v-if="sortKey === 'matched_amount'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('avg_price_matched')" class="cursor-pointer hover:text-teal-400 transition-colors">Odds <span v-if="sortKey === 'avg_price_matched'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('bsp')" class="cursor-pointer hover:text-teal-400 transition-colors">BSP <span v-if="sortKey === 'bsp'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('bsp_diff_absolute')" class="cursor-pointer hover:text-teal-400 transition-colors">BSP Diff <span v-if="sortKey === 'bsp_diff_absolute'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('bsp_diff_percentage')" class="cursor-pointer hover:text-teal-400 transition-colors">BSP % <span v-if="sortKey === 'bsp_diff_percentage'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('bsp_diff_probability')" class="cursor-pointer hover:text-teal-400 transition-colors">BSP Prob <span v-if="sortKey === 'bsp_diff_probability'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('lay_liability')" class="cursor-pointer hover:text-teal-400 transition-colors">Liability <span v-if="sortKey === 'lay_liability'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('profit_loss')" class="cursor-pointer hover:text-teal-400 transition-colors">P/L <span v-if="sortKey === 'profit_loss'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('market_type')" class="cursor-pointer hover:text-teal-400 transition-colors">Market <span v-if="sortKey === 'market_type'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th @click="sort('competition')" class="cursor-pointer hover:text-teal-400 transition-colors">Competition <span v-if="sortKey === 'competition'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span></th>
            <th class="text-center">Del</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bet in bets" :key="bet.id">
            <td class="whitespace-nowrap text-gray-500 font-mono text-xs">{{ formatDate(bet.settled_date) }}</td>
            <td class="whitespace-nowrap text-gray-500 font-mono text-xs">{{ formatTime(bet.description) }}</td>
            <td class="text-gray-600 dark:text-gray-300 max-w-[150px] truncate" :title="bet.description || ''">{{ formatEventName(bet.description) }}</td>
            <td class="whitespace-nowrap text-gray-600 dark:text-gray-300">{{ bet.selection }}</td>
            <td class="text-gray-600 dark:text-gray-300 max-w-[120px] truncate" :title="bet.event || ''">{{ bet.event }}</td>
            <td class="text-gray-600 dark:text-gray-300 max-w-[140px] truncate" :title="bet.strategy || ''">{{ bet.strategy }}</td>
            <td v-if="isDedup" class="text-center">
              <span
                v-if="bet.strategy_count && bet.strategy_count > 1"
                class="inline-flex items-center justify-center min-w-[22px] px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/15 text-amber-500 border border-amber-500/20 cursor-help"
                :title="bet.strategies_triggered ? bet.strategies_triggered.join('\n') : ''"
              >{{ bet.strategy_count }}</span>
              <span v-else class="text-[10px] text-gray-500 font-mono">1</span>
            </td>
            <td class="whitespace-nowrap">
              <span class="px-2 py-0.5 text-[10px] font-bold uppercase rounded-md" :class="bet.bet_type === 'BACK' ? 'bg-sky-500/15 text-sky-400 border border-sky-500/20' : 'bg-rose-500/15 text-rose-400 border border-rose-500/20'">{{ bet.bet_type }}</span>
            </td>
            <td class="whitespace-nowrap font-mono">
              <div v-if="isCustomStaking && bet.recalculated_stake">
                <div class="font-semibold text-sky-400">£{{ bet.recalculated_stake.toFixed(2) }}</div>
                <div class="text-[10px] text-gray-600 line-through">£{{ bet.matched_amount?.toFixed(2) }}</div>
              </div>
              <div v-else class="text-gray-400">£{{ bet.matched_amount?.toFixed(2) }}</div>
            </td>
            <td class="whitespace-nowrap font-mono text-gray-400">{{ bet.avg_price_matched?.toFixed(2) }}</td>
            <td class="whitespace-nowrap font-mono text-gray-400">{{ bet.bsp?.toFixed(2) || '-' }}</td>
            <td class="whitespace-nowrap font-mono" :class="(bet.bsp_diff_absolute || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ bet.bsp_diff_absolute ? ((bet.bsp_diff_absolute > 0 ? '+' : '') + bet.bsp_diff_absolute.toFixed(3)) : '-' }}
            </td>
            <td class="whitespace-nowrap font-mono" :class="(bet.bsp_diff_percentage || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ bet.bsp_diff_percentage ? ((bet.bsp_diff_percentage > 0 ? '+' : '') + bet.bsp_diff_percentage.toFixed(2) + '%') : '-' }}
            </td>
            <td class="whitespace-nowrap font-mono" :class="(bet.bsp_diff_probability || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ bet.bsp_diff_probability ? ((bet.bsp_diff_probability > 0 ? '+' : '') + bet.bsp_diff_probability.toFixed(2) + '%') : '-' }}
            </td>
            <td class="whitespace-nowrap font-mono">
              <div v-if="isCustomStaking && bet.recalculated_liability !== undefined">
                <div class="font-semibold text-sky-400">£{{ bet.recalculated_liability.toFixed(2) }}</div>
                <div class="text-[10px] text-gray-600 line-through">{{ bet.lay_liability ? '£' + bet.lay_liability.toFixed(2) : '-' }}</div>
              </div>
              <div v-else class="text-gray-400">{{ bet.lay_liability ? '£' + bet.lay_liability.toFixed(2) : '-' }}</div>
            </td>
            <td class="whitespace-nowrap font-mono font-semibold">
              <div v-if="isCustomStaking && bet.recalculated_pl !== undefined">
                <div :class="bet.recalculated_pl >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">£{{ bet.recalculated_pl.toFixed(2) }}</div>
                <div class="text-[10px] text-gray-600 line-through font-normal">£{{ bet.profit_loss?.toFixed(2) }}</div>
              </div>
              <div v-else :class="(bet.profit_loss || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">£{{ bet.profit_loss?.toFixed(2) }}</div>
            </td>
            <td class="whitespace-nowrap text-gray-500">{{ bet.market_type }}</td>
            <td class="text-gray-500 max-w-[120px] truncate" :title="bet.competition || ''">{{ bet.competition }}</td>
            <td class="text-center">
              <button @click="handleDelete(bet)" :disabled="deletingId === bet.id" title="Soft-delete this bet" class="p-1 rounded text-gray-600 hover:text-rose-400 hover:bg-rose-500/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                <svg v-if="deletingId !== bet.id" xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
              </button>
            </td>
          </tr>
          <tr v-if="!bets || bets.length === 0">
            <td :colspan="isDedup ? 19 : 18" class="px-6 py-8 text-center text-sm text-gray-600">No bets found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-800/60 text-center">
      <span class="text-xs text-gray-600 font-mono">Showing {{ bets.length }} of {{ totalBets.toLocaleString() }} bets</span>
    </div>
  </div>
</template>

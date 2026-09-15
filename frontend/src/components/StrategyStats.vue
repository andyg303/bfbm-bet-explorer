<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useBetStore } from '../stores/betStore'
import { useAuthStore } from '../stores/authStore'
import type { StrategyStats } from '../services/api'
import StrategyFilters from './StrategyFilters.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import LoadingOverlay from './LoadingOverlay.vue'
import StrategyComparison from './StrategyComparison.vue'

const betStore = useBetStore()
const auth = useAuthStore()

const sortKey = ref<keyof StrategyStats>('total_pl')
const sortDirection = ref<'asc' | 'desc'>('desc')
const selectedStrategies = ref<Set<string>>(new Set())
const showArchiveDialog = ref(false)
const archiving = ref(false)
const showMetricsHelp = ref(false)
const showComparison = ref(false)
const showStrategyList = ref(true)
const comparisonSection = ref<HTMLElement | null>(null)
const showGroupMenu = ref(false)
const newGroupName = ref('')
const groupActionLoading = ref(false)
const groupActionResult = ref<{ type: 'success' | 'error'; message: string } | null>(null)
let groupActionResultTimer: ReturnType<typeof setTimeout> | null = null

const strategyFilters = ref({
  nameSearch: '',
  minBets: null as number | null,
  maxBets: null as number | null,
  minPL: null as number | null,
  maxPL: null as number | null,
  minROI: null as number | null,
  maxROI: null as number | null,
  minWinRate: null as number | null,
  maxWinRate: null as number | null,
  minBspFill: null as number | null,
  maxBspFill: null as number | null
})

const stats = computed(() => {
  const data = betStore.strategyStats || []
  if (!data.length) return data
  
  // Apply frontend filters
  let filtered = data
  
  // Name search
  if (strategyFilters.value.nameSearch) {
    const search = strategyFilters.value.nameSearch.toLowerCase()
    filtered = filtered.filter(stat => stat.strategy.toLowerCase().includes(search))
  }
  
  // Bets range
  if (strategyFilters.value.minBets !== null) {
    filtered = filtered.filter(stat => stat.num_bets >= strategyFilters.value.minBets!)
  }
  if (strategyFilters.value.maxBets !== null) {
    filtered = filtered.filter(stat => stat.num_bets <= strategyFilters.value.maxBets!)
  }
  
  // P/L range
  if (strategyFilters.value.minPL !== null) {
    filtered = filtered.filter(stat => stat.total_pl >= strategyFilters.value.minPL!)
  }
  if (strategyFilters.value.maxPL !== null) {
    filtered = filtered.filter(stat => stat.total_pl <= strategyFilters.value.maxPL!)
  }
  
  // ROI range
  if (strategyFilters.value.minROI !== null) {
    filtered = filtered.filter(stat => stat.roi >= strategyFilters.value.minROI!)
  }
  if (strategyFilters.value.maxROI !== null) {
    filtered = filtered.filter(stat => stat.roi <= strategyFilters.value.maxROI!)
  }
  
  // Win Rate range
  if (strategyFilters.value.minWinRate !== null) {
    filtered = filtered.filter(stat => stat.win_rate >= strategyFilters.value.minWinRate!)
  }
  if (strategyFilters.value.maxWinRate !== null) {
    filtered = filtered.filter(stat => stat.win_rate <= strategyFilters.value.maxWinRate!)
  }
  
  // BSP Fill % range
  if (strategyFilters.value.minBspFill !== null) {
    filtered = filtered.filter(stat => stat.bsp_fill_pct >= strategyFilters.value.minBspFill!)
  }
  if (strategyFilters.value.maxBspFill !== null) {
    filtered = filtered.filter(stat => stat.bsp_fill_pct <= strategyFilters.value.maxBspFill!)
  }
  
  // Sort the filtered data
  const sorted = [...filtered].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    
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

const selectedComparisonStats = computed(() => {
  return stats.value.filter(stat => selectedStrategies.value.has(stat.strategy))
})

function sort(key: keyof StrategyStats) {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'desc'
  }
}

function formatMoney(value: number | null | undefined) {
  return (value ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function valueClass(value: number | null | undefined) {
  return (value ?? 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
}

function toggleStrategy(strategy: string) {
  if (selectedStrategies.value.has(strategy)) {
    selectedStrategies.value.delete(strategy)
  } else {
    selectedStrategies.value.add(strategy)
  }
}

function toggleAll() {
  if (selectedStrategies.value.size === stats.value.length) {
    selectedStrategies.value.clear()
  } else {
    selectedStrategies.value = new Set(stats.value.map(s => s.strategy))
  }
}

function applySelection() {
  betStore.strategyGroupFilter = ''
  betStore.filters.strategies = Array.from(selectedStrategies.value)
}

async function showSelectedComparison() {
  if (selectedStrategies.value.size < 2) return
  showComparison.value = true
  await nextTick()
  comparisonSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function clearSelection() {
  selectedStrategies.value.clear()
  betStore.stakingParams = {
    staking_type: 'default',
    base_stake: 10,
    deduplicate: false,
  }
  betStore.strategyGroupFilter = ''
  betStore.filters.strategies = []
  betStore.refreshAll()
}

function clearFilters() {
  betStore.stakingParams = {
    staking_type: 'default',
    base_stake: 10,
    deduplicate: false,
  }
  strategyFilters.value = {
    nameSearch: '',
    minBets: null,
    maxBets: null,
    minPL: null,
    maxPL: null,
    minROI: null,
    maxROI: null,
    minWinRate: null,
    maxWinRate: null,
    minBspFill: null,
    maxBspFill: null
  }
  if (betStore.strategyGroupFilter) {
    betStore.applyGroupFilter('')
  }
}

function isStarred(strategy: string) {
  return betStore.starredStrategies.has(strategy)
}

function toggleStar(strategy: string) {
  if (auth.isImpersonating) return
  betStore.toggleStarred(strategy)
}

function showGroupActionResult(type: 'success' | 'error', message: string) {
  groupActionResult.value = { type, message }
  if (groupActionResultTimer) clearTimeout(groupActionResultTimer)
  groupActionResultTimer = setTimeout(() => {
    groupActionResult.value = null
  }, 4000)
}

async function addSelectionToGroup(groupId: number) {
  if (auth.isImpersonating) return
  groupActionLoading.value = true
  try {
    const group = await betStore.addToGroup(groupId, Array.from(selectedStrategies.value))
    showGroupActionResult('success', `Added ${selectedStrategies.value.size} strateg${selectedStrategies.value.size === 1 ? 'y' : 'ies'} to "${group.name}"`)
    showGroupMenu.value = false
    newGroupName.value = ''
  } catch {
    showGroupActionResult('error', betStore.error || 'Failed to update group')
  } finally {
    groupActionLoading.value = false
  }
}

async function createGroupAndAddSelection() {
  if (auth.isImpersonating) return
  const name = newGroupName.value.trim()
  if (!name) return
  groupActionLoading.value = true
  try {
    const group = await betStore.createGroup(name)
    if (group) {
      await betStore.addToGroup(group.id, Array.from(selectedStrategies.value))
      showGroupActionResult('success', `Added ${selectedStrategies.value.size} strateg${selectedStrategies.value.size === 1 ? 'y' : 'ies'} to "${group.name}"`)
      showGroupMenu.value = false
      newGroupName.value = ''
    }
  } catch {
    showGroupActionResult('error', betStore.error || 'Failed to create group')
  } finally {
    groupActionLoading.value = false
  }
}

async function archiveSelected() {
  if (auth.isImpersonating) return
  showArchiveDialog.value = false
  archiving.value = true
  try {
    await betStore.archiveStrategies(Array.from(selectedStrategies.value))
    selectedStrategies.value.clear()
  } finally {
    archiving.value = false
  }
}

watch(selectedStrategies, () => {
  if (selectedStrategies.value.size < 2) {
    showComparison.value = false
  }
}, { deep: true })
</script>

<template>
  <div class="space-y-6">
    <div class="glass-card">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-white/5">
        <div class="flex justify-between items-center mb-4">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
              <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h2 class="text-base font-semibold text-gray-900 dark:text-white tracking-tight">Strategy Performance</h2>
          </div>
          <div class="flex flex-wrap justify-end gap-2">
            <button
              v-if="selectedStrategies.size > 0"
              @click="showSelectedComparison"
              :disabled="selectedStrategies.size < 2"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-sky-500 dark:text-sky-400 bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
              title="Compare selected strategies"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              Compare ({{ selectedStrategies.size }})
            </button>
            <div v-if="!auth.isImpersonating" class="relative">
              <button
                @click="showGroupMenu = !showGroupMenu"
                :disabled="selectedStrategies.size < 2"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-violet-500 dark:text-violet-400 bg-violet-500/10 border border-violet-500/20 hover:bg-violet-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
                title="Add selected strategies to a group"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Add to Group ({{ selectedStrategies.size }})
              </button>
              <Transition enter-active-class="transition ease-out duration-100" enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100" leave-active-class="transition ease-in duration-75" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
                <div v-if="showGroupMenu" class="absolute right-0 mt-2 w-64 rounded-xl bg-white dark:bg-[#111827] border border-gray-200 dark:border-gray-800 shadow-xl z-50 overflow-hidden">
                  <div class="px-3 py-2 border-b border-gray-100 dark:border-gray-800">
                    <p class="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Add {{ selectedStrategies.size }} to group</p>
                  </div>
                  <div v-if="betStore.strategyGroups.length" class="max-h-44 overflow-y-auto py-1">
                    <button
                      v-for="group in betStore.strategyGroups"
                      :key="group.id"
                      @click="addSelectionToGroup(group.id)"
                      :disabled="groupActionLoading"
                      class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/50 flex items-center justify-between gap-2 transition-colors disabled:opacity-50"
                    >
                      <span class="truncate">{{ group.name }}</span>
                      <span class="text-[10px] text-gray-400 font-mono">{{ group.strategies.length }}</span>
                    </button>
                  </div>
                  <p v-else class="px-3 py-2 text-xs text-gray-400">No groups yet</p>
                  <div class="border-t border-gray-100 dark:border-gray-800 p-2 flex gap-1.5">
                    <input
                      v-model="newGroupName"
                      @keyup.enter="createGroupAndAddSelection"
                      type="text"
                      placeholder="New group name…"
                      maxlength="100"
                      class="input-field !py-1 !text-xs flex-1 min-w-0"
                    >
                    <button
                      @click="createGroupAndAddSelection"
                      :disabled="!newGroupName.trim() || groupActionLoading"
                      class="px-2.5 py-1 text-xs font-medium text-white bg-violet-500 hover:bg-violet-400 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors"
                    >
                      Create
                    </button>
                  </div>
                </div>
              </Transition>
            </div>
            <button
              v-if="!auth.isImpersonating"
              @click="showArchiveDialog = true"
              :disabled="selectedStrategies.size === 0"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
              Archive ({{ selectedStrategies.size }})
            </button>
            <button
              @click="applySelection"
              :disabled="selectedStrategies.size === 0"
              class="px-3 py-1.5 text-xs font-medium text-teal-400 bg-teal-500/10 border border-teal-500/20 hover:bg-teal-500/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all"
            >
              Apply ({{ selectedStrategies.size }})
            </button>
            <button
              @click="clearSelection"
              class="px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-white/5 border border-gray-300 dark:border-white/10 hover:bg-gray-200 dark:hover:bg-white/10 rounded-lg transition-all"
            >
              Clear
            </button>
          </div>
        </div>
        <StrategyFilters v-model="strategyFilters" @clear="clearFilters" />

        <!-- Group action feedback toast -->
        <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-2">
          <div v-if="groupActionResult" class="mt-3 p-2.5 rounded-lg text-xs font-medium" :class="groupActionResult.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 dark:text-emerald-400' : 'bg-rose-500/10 border border-rose-500/20 text-rose-500 dark:text-rose-400'">
            {{ groupActionResult.message }}
          </div>
        </Transition>
      </div>

      <!-- Click-outside backdrop for the Add to Group menu -->
      <div v-if="showGroupMenu" class="fixed inset-0 z-40" @click="showGroupMenu = false" />

      <!-- Strategy list controls -->
      <div class="border-t border-gray-200 dark:border-gray-800/60">
        <div class="flex flex-col gap-2 px-4 py-2.5 sm:flex-row sm:items-center sm:justify-between">
          <button
            @click="showStrategyList = !showStrategyList"
            class="inline-flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-teal-500 dark:hover:text-teal-400 transition-colors"
          >
            <svg class="w-3.5 h-3.5 transition-transform" :class="{ 'rotate-180': showStrategyList }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            {{ showStrategyList ? 'Hide Strategy List' : 'Show Strategy List' }}
          </button>

          <button
            @click="showMetricsHelp = !showMetricsHelp"
            class="inline-flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 hover:text-teal-500 dark:hover:text-teal-400 transition-colors sm:justify-end"
          >
            <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span class="font-medium">What is ROI % vs Reverse ROI %?</span>
            <span class="text-[10px] font-mono text-gray-400 dark:text-gray-600">{{ showMetricsHelp ? 'hide ▲' : 'show ▼' }}</span>
          </button>
        </div>
        <transition name="help-slide">
          <div v-if="showMetricsHelp" class="px-4 pb-4 pt-1 text-xs text-gray-600 dark:text-gray-400 space-y-2.5 border-t border-gray-100 dark:border-gray-800/40">
            <p>Both measure profit relative to risk, but use a different denominator depending on bet side:</p>
            <div class="ml-3 space-y-1.5">
              <p><span class="font-medium text-teal-500">ROI %</span> = profit ÷ <em>what you actually risked</em>. BACK: stake. LAY: liability — <code>(odds − 1) × stake</code>.</p>
              <p><span class="font-medium text-teal-500">Reverse ROI %</span> = profit ÷ <em>what the opposite side would have risked</em>. BACK: would-be lay liability. LAY: the stake.</p>
            </div>
            <p>They only diverge when odds are far from 2.0. At exactly 2.0 they are identical.</p>
            <div class="p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-300">
              <p class="font-medium mb-1">Example — lay-the-longshot (101.0 odds, +£90 profit from 1,000 bets)</p>
              <ul class="ml-4 list-disc space-y-0.5">
                <li><span class="font-medium">ROI %</span>: £90 ÷ £100,000 liability = <span class="font-mono">0.09%</span> — does not look very promising!</li>
                <li><span class="font-medium">Reverse ROI %</span>: £90 ÷ £1,000 stakes = <span class="font-mono">9.0%</span> — reveals the real edge.</li>
              </ul>
            </div>
            <p class="text-[10px] text-gray-500 italic">Rule of thumb: ROI % = bankroll efficiency. Reverse ROI % = edge per pound of other-side exposure.</p>
          </div>
        </transition>
      </div>

      <!-- Table -->
      <div v-if="showStrategyList" class="overflow-x-auto">
        <table class="data-table">
        <thead>
          <tr>
            <th class="!px-4 !w-10">
              <input 
                type="checkbox" 
                :checked="selectedStrategies.size === stats.length && stats.length > 0"
                @change="toggleAll"
                class="rounded border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-white/5 text-teal-500 focus:ring-teal-500/30 focus:ring-offset-0"
              >
            </th>
            <th class="!w-10 !px-2" title="Starred">
              <svg class="w-3.5 h-3.5 mx-auto text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
            </th>
            <th @click="sort('strategy')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Strategy <span v-if="sortKey === 'strategy'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('num_bets')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Bets <span v-if="sortKey === 'num_bets'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('gross_pl')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Gross P/L <span v-if="sortKey === 'gross_pl'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('commission_paid')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Comm. Paid <span v-if="sortKey === 'commission_paid'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('total_pl')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Net P/L <span v-if="sortKey === 'total_pl'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('roi')" class="cursor-pointer hover:text-teal-400 transition-colors" title="Profit ÷ actual risk (BACK: stake; LAY: liability). Click the (i) icon above for examples.">
              ROI % <span v-if="sortKey === 'roi'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('yield_pct')" class="cursor-pointer hover:text-teal-400 transition-colors" title="Profit ÷ opposite-side risk (BACK: would-be lay liability; LAY: stake). Useful for spotting edges at extreme odds. Click the (i) icon above for examples.">
              Reverse ROI % <span v-if="sortKey === 'yield_pct'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('total_staked')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Staked <span v-if="sortKey === 'total_staked'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_odds')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Avg Odds <span v-if="sortKey === 'avg_odds'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('win_rate')" class="cursor-pointer hover:text-teal-400 transition-colors">
              Win Rate <span v-if="sortKey === 'win_rate'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th>Back/Lay</th>
            <th @click="sort('bsp_fill_pct')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP Fill % <span v-if="sortKey === 'bsp_fill_pct'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_abs')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP Abs <span v-if="sortKey === 'avg_bsp_abs'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_pct')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP % <span v-if="sortKey === 'avg_bsp_pct'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th @click="sort('avg_bsp_prob')" class="cursor-pointer hover:text-teal-400 transition-colors">
              BSP Prob <span v-if="sortKey === 'avg_bsp_prob'" class="text-teal-400">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stat in stats" :key="stat.strategy">
            <td class="!px-4">
              <input 
                type="checkbox" 
                :checked="selectedStrategies.has(stat.strategy)"
                @change="toggleStrategy(stat.strategy)"
                class="rounded border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-white/5 text-teal-500 focus:ring-teal-500/30 focus:ring-offset-0"
              >
            </td>
            <td class="!px-2">
              <button
                @click="toggleStar(stat.strategy)"
                :disabled="auth.isImpersonating"
                :title="isStarred(stat.strategy) ? 'Remove star' : 'Star strategy'"
                class="p-0.5 rounded transition-colors disabled:cursor-default"
                :class="isStarred(stat.strategy) ? 'text-amber-400 hover:text-amber-300' : 'text-gray-300 dark:text-gray-600 hover:text-amber-400'"
              >
                <svg class="w-4 h-4" :fill="isStarred(stat.strategy) ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                </svg>
              </button>
            </td>
            <td class="strategy-cell font-medium text-gray-900 dark:text-white">{{ stat.strategy }}</td>
            <td class="font-mono">{{ stat.num_bets }}</td>
            <td class="font-mono font-medium" :class="valueClass(stat.gross_pl ?? stat.total_pl)">
              £{{ formatMoney(stat.gross_pl ?? stat.total_pl) }}
            </td>
            <td class="font-mono text-amber-500 dark:text-amber-400">
              £{{ formatMoney(stat.commission_paid) }}
            </td>
            <td class="font-mono font-medium" :class="valueClass(stat.net_pl ?? stat.total_pl)">
              £{{ formatMoney(stat.net_pl ?? stat.total_pl) }}
            </td>
            <td class="font-mono" :class="stat.roi >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ stat.roi }}%
            </td>
            <td class="font-mono" :class="stat.yield_pct >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ stat.yield_pct.toFixed(2) }}%
            </td>
            <td class="font-mono text-gray-400">£{{ stat.total_staked.toLocaleString() }}</td>
            <td class="font-mono text-gray-400">{{ stat.avg_odds.toFixed(2) }}</td>
            <td class="font-mono text-gray-400">{{ stat.win_rate.toFixed(1) }}%</td>
            <td class="font-mono text-gray-400">{{ stat.num_back }}/{{ stat.num_lay }}</td>
            <td class="font-mono text-gray-400">{{ stat.bsp_fill_pct.toFixed(1) }}%</td>
            <td class="font-mono" :class="stat.avg_bsp_abs >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ stat.avg_bsp_abs > 0 ? '+' : '' }}{{ stat.avg_bsp_abs.toFixed(3) }}
            </td>
            <td class="font-mono" :class="stat.avg_bsp_pct >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ stat.avg_bsp_pct > 0 ? '+' : '' }}{{ stat.avg_bsp_pct.toFixed(2) }}%
            </td>
            <td class="font-mono" :class="stat.avg_bsp_prob >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'">
              {{ stat.avg_bsp_prob > 0 ? '+' : '' }}{{ stat.avg_bsp_prob.toFixed(2) }}%
            </td>
          </tr>
          <tr v-if="!stats || stats.length === 0">
            <td colspan="17" class="!py-12 text-center text-sm text-gray-500">No strategies match the filters</td>
          </tr>
        </tbody>
      </table>
    </div>
    </div>

    <div v-if="showComparison && selectedComparisonStats.length >= 2" ref="comparisonSection">
      <StrategyComparison
        :strategies="selectedComparisonStats"
        @close="showComparison = false"
      />
    </div>

    <!-- Archive Confirmation Dialog -->
    <ConfirmDialog
      :open="showArchiveDialog"
      title="Archive Strategies"
      :message="`Are you sure you want to archive ${selectedStrategies.size} strateg${selectedStrategies.size === 1 ? 'y' : 'ies'}? All bets within ${selectedStrategies.size === 1 ? 'it' : 'them'} will be hidden from the dashboard. You can restore them at any time from the Archive.`"
      confirm-label="Archive"
      cancel-label="Cancel"
      variant="warning"
      icon="archive"
      @confirm="archiveSelected"
      @cancel="showArchiveDialog = false"
    />

    <LoadingOverlay
      :show="archiving"
      title="Archiving strategies…"
      message="Hiding the selected strategies and recalculating stats. This can take up to a minute for large data sets — please wait."
    />
  </div>
</template>

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { FilterParams, StrategyStats, Bet, PLDataPoint, OddsBandProfit, OddsCurvePoint, MonthlyPLResponse, ArchivedStrategy, MergeSuggestion, StrategyInfo } from '../services/api'
import * as api from '../services/api'

type LoadingSection = 'filters' | 'summary' | 'strategies' | 'bets' | 'plGraph' | 'monthly' | 'oddsBands' | 'archive' | 'mergeSuggestions'
type LoadingSections = Record<LoadingSection, boolean>
type LoadingSectionCounts = Record<LoadingSection, number>

function createLoadingSections(): LoadingSections {
  return {
    filters: false,
    summary: false,
    strategies: false,
    bets: false,
    plGraph: false,
    monthly: false,
    oddsBands: false,
    archive: false,
    mergeSuggestions: false,
  }
}

function createLoadingSectionCounts(): LoadingSectionCounts {
  return {
    filters: 0,
    summary: 0,
    strategies: 0,
    bets: 0,
    plGraph: 0,
    monthly: 0,
    oddsBands: 0,
    archive: 0,
    mergeSuggestions: 0,
  }
}

export const useBetStore = defineStore('bet', () => {
  const filterOptions = ref<any>(null)
  const strategyStats = ref<StrategyStats[]>([])
  const bets = ref<Bet[]>([])
  const totalBets = ref(0)
  const plOverTime = ref<PLDataPoint[]>([])
  const summaryStats = ref<any>(null)
  const oddsBandsData = ref<OddsBandProfit[]>([])
  const oddsCurveData = ref<OddsCurvePoint[]>([])
  const monthlyPLData = ref<MonthlyPLResponse | null>(null)
  const archivedStrategies = ref<ArchivedStrategy[]>([])
  const mergeSuggestions = ref<MergeSuggestion[]>([])
  const allStrategies = ref<StrategyInfo[]>([])
  const loading = ref(false)
  const loadingSections = ref<LoadingSections>(createLoadingSections())
  const error = ref<string | null>(null)
  const loadingSectionCounts = createLoadingSectionCounts()
  let activeLoads = 0

  const filters = ref<FilterParams>({
    strategies: [],
    bet_types: [],
    statuses: [],
    market_types: [],
    country_codes: [],
    events: [],
  })

  const stakingParams = ref({
    staking_type: 'default',
    base_stake: 10,
    deduplicate: false,
  })

  const recalculatedStats = ref<any>(null)
  const strategySearchFilter = ref('')

  function startLoading(section?: LoadingSection) {
    activeLoads += 1
    loading.value = true
    if (section) {
      loadingSectionCounts[section] += 1
      loadingSections.value[section] = true
    }
  }

  function finishLoading(section?: LoadingSection) {
    if (section) {
      loadingSectionCounts[section] = Math.max(0, loadingSectionCounts[section] - 1)
      loadingSections.value[section] = loadingSectionCounts[section] > 0
    }
    activeLoads = Math.max(0, activeLoads - 1)
    loading.value = activeLoads > 0
  }

  async function withLoading<T>(section: LoadingSection | null, action: () => Promise<T>) {
    startLoading(section ?? undefined)
    try {
      return await action()
    } catch (e: any) {
      error.value = e.message
    } finally {
      finishLoading(section ?? undefined)
    }
  }

  async function loadFilterOptions() {
    return withLoading('filters', async () => {
      filterOptions.value = await api.getFilterOptions()
    })
  }

  async function loadStrategyStats() {
    return withLoading('strategies', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      strategyStats.value = await api.getStrategyStats(filtersWithStaking)
    })
  }

  async function loadBets(skip: number = 0, limit: number = 100, sortBy: string = 'start_time', sortDir: string = 'desc') {
    return withLoading('bets', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      const response = await api.getBets(filtersWithStaking, skip, limit, sortBy, sortDir)
      bets.value = response.bets
      totalBets.value = response.total
    })
  }

  async function loadPLOverTime() {
    return withLoading('plGraph', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      plOverTime.value = await api.getPLOverTime(filtersWithStaking)
    })
  }

  async function loadSummaryStats() {
    return withLoading('summary', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      summaryStats.value = await api.getSummaryStats(filtersWithStaking)
    })
  }

  async function loadOddsBandsData() {
    return withLoading('oddsBands', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      oddsBandsData.value = await api.getOddsBandsProfit(filtersWithStaking)
    })
  }

  async function loadOddsCurveData() {
    try {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      oddsCurveData.value = await api.getProfitCurveByOdds(filtersWithStaking)
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function loadMonthlyPL() {
    return withLoading('monthly', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      monthlyPLData.value = await api.getMonthlyPL(filtersWithStaking)
    })
  }

  async function recalculateWithStaking() {
    return withLoading(null, async () => {
      recalculatedStats.value = await api.recalculateStaking(filters.value, stakingParams.value)
    })
  }

  async function deleteBet(id: number) {
    try {
      await api.deleteBet(id)
      // Remove from local list immediately for a snappy UI, then refresh stats
      bets.value = bets.value.filter((b) => b.id !== id)
      totalBets.value = Math.max(0, totalBets.value - 1)
      await refreshAll()
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function archiveStrategies(strategies: string[]) {
    startLoading()
    try {
      await api.archiveStrategies(strategies)
      await loadFilterOptions()
      await refreshAll()
      await loadArchivedStrategies()
    } catch (e: any) {
      error.value = e.message
    } finally {
      finishLoading()
    }
  }

  async function restoreStrategies(strategies: string[]) {
    startLoading()
    try {
      await api.restoreStrategies(strategies)
      await loadFilterOptions()
      await refreshAll()
      await loadArchivedStrategies()
    } catch (e: any) {
      error.value = e.message
    } finally {
      finishLoading()
    }
  }

  async function deleteArchivedStrategies(strategies: string[]) {
    startLoading()
    try {
      await api.deleteArchivedStrategies(strategies)
      await loadArchivedStrategies()
    } catch (e: any) {
      error.value = e.message
    } finally {
      finishLoading()
    }
  }

  async function loadArchivedStrategies() {
    return withLoading('archive', async () => {
      archivedStrategies.value = await api.getArchivedStrategies()
    })
  }

  async function sanitizeStrategies() {
    startLoading()
    try {
      const result = await api.sanitizeStrategies()
      if (result.rows_fixed > 0) {
        await loadFilterOptions()
        await refreshAll()
      }
      return result
    } catch (e: any) {
      error.value = e.message
    } finally {
      finishLoading()
    }
  }

  async function migrateDeletedToArchived() {
    try {
      const result = await api.migrateDeletedToArchived()
      if (result.migrated_bets > 0) {
        await loadFilterOptions()
        await refreshAll()
        await loadArchivedStrategies()
      }
      return result
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function loadMergeSuggestions() {
    return withLoading('mergeSuggestions', async () => {
      mergeSuggestions.value = await api.getMergeSuggestions()
    })
  }

  async function loadAllStrategies() {
    try {
      allStrategies.value = await api.getAllStrategies()
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function mergeStrategies(sourceStrategies: string[], targetStrategy: string) {
    startLoading()
    try {
      const result = await api.mergeStrategies(sourceStrategies, targetStrategy)
      // Refresh everything after merge
      await loadFilterOptions()
      await refreshAll()
      await loadAllStrategies()
      await loadMergeSuggestions()
      return result
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      finishLoading()
    }
  }

  async function deleteMergeDuplicateBets(targetStrategy: string, betIds: number[]) {
    startLoading()
    try {
      const result = await api.deleteMergeDuplicateBets(targetStrategy, betIds)
      await loadFilterOptions()
      await refreshAll()
      await loadAllStrategies()
      await loadMergeSuggestions()
      return result
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      finishLoading()
    }
  }

  async function refreshAll() {
    await Promise.all([
      loadSummaryStats(),
      loadStrategyStats(),
      loadBets(),
      loadPLOverTime(),
      loadOddsBandsData(),
      loadMonthlyPL(),
    ])
  }

  return {
    filterOptions,
    strategyStats,
    bets,
    totalBets,
    plOverTime,
    summaryStats,
    oddsBandsData,
    oddsCurveData,
    monthlyPLData,
    archivedStrategies,
    mergeSuggestions,
    allStrategies,
    loading,
    loadingSections,
    error,
    filters,
    stakingParams,
    recalculatedStats,
    strategySearchFilter,
    loadFilterOptions,
    loadStrategyStats,
    loadBets,
    loadPLOverTime,
    loadSummaryStats,
    loadOddsBandsData,
    loadOddsCurveData,
    loadMonthlyPL,
    recalculateWithStaking,
    deleteBet,
    archiveStrategies,
    restoreStrategies,
    deleteArchivedStrategies,
    loadArchivedStrategies,
    sanitizeStrategies,
    migrateDeletedToArchived,
    loadMergeSuggestions,
    loadAllStrategies,
    mergeStrategies,
    deleteMergeDuplicateBets,
    refreshAll,
  }
})

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { FilterParams, StrategyStats, Bet, PLDataPoint, OddsBandProfit, MonthlyPLResponse, ArchivedStrategy } from '../services/api'
import * as api from '../services/api'

export const useBetStore = defineStore('bet', () => {
  const filterOptions = ref<any>(null)
  const strategyStats = ref<StrategyStats[]>([])
  const bets = ref<Bet[]>([])
  const totalBets = ref(0)
  const plOverTime = ref<PLDataPoint[]>([])
  const summaryStats = ref<any>(null)
  const oddsBandsData = ref<OddsBandProfit[]>([])
  const monthlyPLData = ref<MonthlyPLResponse | null>(null)
  const archivedStrategies = ref<ArchivedStrategy[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

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
  })

  const recalculatedStats = ref<any>(null)
  const strategySearchFilter = ref('')

  async function loadFilterOptions() {
    try {
      loading.value = true
      filterOptions.value = await api.getFilterOptions()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadStrategyStats() {
    try {
      loading.value = true
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      strategyStats.value = await api.getStrategyStats(filtersWithStaking)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadBets(skip: number = 0, limit: number = 100) {
    try {
      loading.value = true
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      const response = await api.getBets(filtersWithStaking, skip, limit)
      bets.value = response.bets
      totalBets.value = response.total
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadPLOverTime() {
    try {
      loading.value = true
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      plOverTime.value = await api.getPLOverTime(filtersWithStaking)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadSummaryStats() {
    try {
      loading.value = true
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      summaryStats.value = await api.getSummaryStats(filtersWithStaking)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadOddsBandsData() {
    try {
      loading.value = true
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      oddsBandsData.value = await api.getOddsBandsProfit(filtersWithStaking)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadMonthlyPL() {
    try {
      loading.value = true
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      monthlyPLData.value = await api.getMonthlyPL(filtersWithStaking)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function recalculateWithStaking() {
    try {
      loading.value = true
      recalculatedStats.value = await api.recalculateStaking(filters.value, stakingParams.value)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
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
    try {
      loading.value = true
      await api.archiveStrategies(strategies)
      await loadFilterOptions()
      await refreshAll()
      await loadArchivedStrategies()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function restoreStrategies(strategies: string[]) {
    try {
      loading.value = true
      await api.restoreStrategies(strategies)
      await loadFilterOptions()
      await refreshAll()
      await loadArchivedStrategies()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadArchivedStrategies() {
    try {
      archivedStrategies.value = await api.getArchivedStrategies()
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function sanitizeStrategies() {
    try {
      loading.value = true
      const result = await api.sanitizeStrategies()
      if (result.rows_fixed > 0) {
        await loadFilterOptions()
        await refreshAll()
      }
      return result
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
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
    monthlyPLData,
    archivedStrategies,
    loading,
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
    loadMonthlyPL,
    recalculateWithStaking,
    deleteBet,
    archiveStrategies,
    restoreStrategies,
    loadArchivedStrategies,
    sanitizeStrategies,
    migrateDeletedToArchived,
    refreshAll,
  }
})

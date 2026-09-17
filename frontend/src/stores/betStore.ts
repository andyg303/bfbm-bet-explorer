import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { FilterParams, StrategyStats, Bet, PLDataPoint, OddsBandProfit, OddsCurvePoint, MonthlyPLResponse, ArchivedStrategy, MergeSuggestion, StrategyInfo, StrategyGroup, PeriodStats } from '../services/api'
import * as api from '../services/api'

type LoadingSection = 'filters' | 'summary' | 'periods' | 'strategies' | 'bets' | 'plGraph' | 'monthly' | 'oddsBands' | 'archive' | 'mergeSuggestions'
type LoadingSections = Record<LoadingSection, boolean>
type LoadingSectionCounts = Record<LoadingSection, number>

function createLoadingSections(): LoadingSections {
  return {
    filters: false,
    summary: false,
    periods: false,
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
    periods: 0,
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
  const periodStats = ref<PeriodStats | null>(null)
  const oddsBandsData = ref<OddsBandProfit[]>([])
  const oddsCurveData = ref<OddsCurvePoint[]>([])
  const monthlyPLData = ref<MonthlyPLResponse | null>(null)
  const archivedStrategies = ref<ArchivedStrategy[]>([])
  const mergeSuggestions = ref<MergeSuggestion[]>([])
  const allStrategies = ref<StrategyInfo[]>([])
  const starredStrategies = ref<Set<string>>(new Set())
  const strategyGroups = ref<StrategyGroup[]>([])
  // '' = no group filter | 'starred' | `group:<id>`
  const strategyGroupFilter = ref('')
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

  async function loadPeriodStats() {
    return withLoading('periods', async () => {
      const filtersWithStaking = { ...filters.value, ...stakingParams.value }
      periodStats.value = await api.getPeriodStats(filtersWithStaking)
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

  // ─── Strategy stars & groups ────────────────────────────────────────────

  // Sentinel strategy name so an empty group/starred selection filters to
  // zero strategies instead of behaving like "no filter".
  const EMPTY_GROUP_SENTINEL = ' __no_strategies__'

  function resolveGroupFilterStrategies(value?: string): string[] {
    const v = value ?? strategyGroupFilter.value
    if (v === 'starred') {
      return Array.from(starredStrategies.value)
    }
    if (v.startsWith('group:')) {
      const group = strategyGroups.value.find(g => g.id === Number(v.slice(6)))
      return group ? [...group.strategies] : []
    }
    return []
  }

  function applyGroupFilter(value?: string) {
    if (value !== undefined) {
      strategyGroupFilter.value = value
    }
    const members = resolveGroupFilterStrategies()
    filters.value = {
      ...filters.value,
      strategies: strategyGroupFilter.value
        ? (members.length ? members : [EMPTY_GROUP_SENTINEL])
        : [],
    }
  }

  async function loadStrategyMeta() {
    try {
      const meta = await api.getStrategyMeta()
      starredStrategies.value = new Set(meta.starred)
      strategyGroups.value = meta.groups
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function toggleStarred(strategy: string) {
    const previous = new Set(starredStrategies.value)
    const next = new Set(previous)
    const nowStarred = !next.has(strategy)
    if (nowStarred) next.add(strategy)
    else next.delete(strategy)
    starredStrategies.value = next
    try {
      await api.setStrategyStarred(strategy, nowStarred)
      if (strategyGroupFilter.value === 'starred') applyGroupFilter()
    } catch (e: any) {
      starredStrategies.value = previous
      error.value = e.message
    }
  }

  function upsertGroup(group: StrategyGroup) {
    const idx = strategyGroups.value.findIndex(g => g.id === group.id)
    if (idx >= 0) strategyGroups.value[idx] = group
    else strategyGroups.value.push(group)
    if (strategyGroupFilter.value === `group:${group.id}`) applyGroupFilter()
  }

  async function createGroup(name: string): Promise<StrategyGroup | undefined> {
    try {
      const group = await api.createStrategyGroup(name)
      upsertGroup(group)
      return group
    } catch (e: any) {
      error.value = e.message
      throw e
    }
  }

  async function addToGroup(groupId: number, strategies: string[]) {
    try {
      const group = await api.addStrategiesToGroup(groupId, strategies)
      upsertGroup(group)
      return group
    } catch (e: any) {
      error.value = e.message
      throw e
    }
  }

  async function removeFromGroup(groupId: number, strategies: string[]) {
    try {
      const group = await api.removeStrategiesFromGroup(groupId, strategies)
      upsertGroup(group)
      return group
    } catch (e: any) {
      error.value = e.message
      throw e
    }
  }

  async function deleteGroup(groupId: number) {
    try {
      await api.deleteStrategyGroup(groupId)
      strategyGroups.value = strategyGroups.value.filter(g => g.id !== groupId)
      if (strategyGroupFilter.value === `group:${groupId}`) {
        applyGroupFilter('')
      }
    } catch (e: any) {
      error.value = e.message
      throw e
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
      await loadStrategyMeta()
      if (strategyGroupFilter.value) applyGroupFilter()
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
      loadPeriodStats(),
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
    periodStats,
    oddsBandsData,
    oddsCurveData,
    monthlyPLData,
    archivedStrategies,
    mergeSuggestions,
    allStrategies,
    starredStrategies,
    strategyGroups,
    strategyGroupFilter,
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
    loadPeriodStats,
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
    loadStrategyMeta,
    toggleStarred,
    createGroup,
    addToGroup,
    removeFromGroup,
    deleteGroup,
    applyGroupFilter,
    mergeStrategies,
    deleteMergeDuplicateBets,
    refreshAll,
  }
})

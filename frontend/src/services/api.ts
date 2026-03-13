import axios from 'axios'

// Docker: VITE_API_URL="/api" → nginx proxies to backend
// Local dev: defaults to 'http://localhost:8000'
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Auth interceptor: attach JWT to every request ───────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bfbm_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Response interceptor: auto-refresh on 401 ──────────────────────────────
let isRefreshing = false
let failedQueue: { resolve: (v: unknown) => void; reject: (e: unknown) => void }[] = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('bfbm_refresh_token')
      if (!refreshToken) {
        // No refresh token — force logout
        localStorage.removeItem('bfbm_access_token')
        localStorage.removeItem('bfbm_refresh_token')
        localStorage.removeItem('bfbm_user')
        window.location.reload()
        return Promise.reject(error)
      }

      try {
        const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })
        const newToken = res.data.access_token
        localStorage.setItem('bfbm_access_token', newToken)
        localStorage.setItem('bfbm_refresh_token', res.data.refresh_token)
        localStorage.setItem('bfbm_user', JSON.stringify(res.data.user))
        processQueue(null, newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('bfbm_access_token')
        localStorage.removeItem('bfbm_refresh_token')
        localStorage.removeItem('bfbm_user')
        window.location.reload()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)

// Export the raw axios instance for direct use (e.g. Stripe checkout)
export { api }

// ─── Type definitions ────────────────────────────────────────────────────────

export interface FilterParams {
  strategies?: string[]
  bet_types?: string[]
  statuses?: string[]
  market_types?: string[]
  country_codes?: string[]
  events?: string[]
  min_odds?: number
  max_odds?: number
  min_stake?: number
  max_stake?: number
  min_pl?: number
  max_pl?: number
  date_from?: string
  date_to?: string
  selection_search?: string
  description_search?: string
}

export interface StakingParams {
  staking_type: string
  base_stake: number
}

export interface StrategyStats {
  strategy: string
  num_bets: number
  total_pl: number
  roi: number
  yield_pct: number
  total_staked: number
  avg_odds: number
  win_rate: number
  num_back: number
  num_lay: number
  bsp_fill_pct: number
  avg_bsp_abs: number
  avg_bsp_pct: number
  avg_bsp_prob: number
}

export interface Bet {
  id: number
  bet_id: string
  description: string | null
  selection: string | null
  bet_type: string | null
  matched_amount: number | null
  avg_price_matched: number | null
  bsp: number | null
  bsp_diff_absolute: number | null
  bsp_diff_percentage: number | null
  bsp_diff_probability: number | null
  status: string | null
  profit_loss: number | null
  strategy: string | null
  settled_date: string | null
  placed_date: string | null
  matched_date: string | null
  market_type: string | null
  lay_liability: number | null
  country_code: string | null
  event: string | null
  competition: string | null
  price_requested: number | null
  recalculated_stake?: number
  recalculated_pl?: number
  recalculated_liability?: number
  is_deleted?: boolean
}

export interface PLDataPoint {
  date: string
  daily_pl: number
  cumulative_pl: number
}

export interface OddsBandProfit {
  band: string
  num_bets: number
  total_pl: number
  total_staked: number
  roi: number
}

export interface MonthlyPLRow {
  year: number
  [month: string]: number | null
}

export interface KeyStats {
  total_profit: number
  monthly_average: number
  monthly_low: number
  monthly_high: number
  winning_months: number
  months_of_data: number
  winning_months_pct: number
  max_absolute_drawdown: number
  max_peak_trough_drawdown: number
}

export interface MonthlyPLResponse {
  grid: MonthlyPLRow[]
  years: number[]
  key_stats: KeyStats
}

// ─── API functions ───────────────────────────────────────────────────────────

export const getFilterOptions = async () => {
  const response = await api.get('/filter-options')
  return response.data
}

export const getStrategyStats = async (filters: FilterParams): Promise<StrategyStats[]> => {
  const response = await api.post('/strategy-stats', filters)
  return response.data
}

export const getBets = async (filters: FilterParams, skip: number = 0, limit: number = 100) => {
  const response = await api.post(`/bets?skip=${skip}&limit=${limit}`, filters)
  return response.data
}

export const getPLOverTime = async (filters: FilterParams): Promise<PLDataPoint[]> => {
  const response = await api.post('/pl-over-time', filters)
  return response.data
}

export const recalculateStaking = async (filters: FilterParams, staking: StakingParams) => {
  const response = await api.post('/recalculate-staking', { ...filters, ...staking })
  return response.data
}

export const getSummaryStats = async (filters: FilterParams) => {
  const response = await api.post('/summary-stats', filters)
  return response.data
}

export const getOddsBandsProfit = async (filters: FilterParams): Promise<OddsBandProfit[]> => {
  const response = await api.post('/odds-bands-profit', filters)
  return response.data
}

export const getMonthlyPL = async (filters: FilterParams): Promise<MonthlyPLResponse> => {
  const response = await api.post('/monthly-pl', filters)
  return response.data
}

export const uploadBetsCSV = async (
  file: File,
  onProgress?: (pct: number) => void,
): Promise<{
  filename: string
  inserted: number
  updated: number
  skipped: number
  total_bets_in_db: number
}> => {
  const formData = new FormData()
  formData.append('file', file)
  const token = localStorage.getItem('bfbm_access_token')
  const response = await axios.post(`${API_BASE_URL}/ingest`, formData, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return response.data
}

export const deleteBet = async (id: number): Promise<void> => {
  await api.delete(`/bets/${id}`)
}

export interface ArchivedStrategy {
  strategy: string
  num_bets: number
  total_pl: number
  total_staked: number
  roi: number
  avg_odds: number
  win_rate: number
  first_bet: string | null
  last_bet: string | null
}

export const archiveStrategies = async (
  strategies: string[],
): Promise<{ archived_bets: number }> => {
  const response = await api.post('/strategies/archive', { strategies })
  return response.data
}

export const restoreStrategies = async (
  strategies: string[],
): Promise<{ restored_bets: number }> => {
  const response = await api.post('/strategies/restore', { strategies })
  return response.data
}

export const getArchivedStrategies = async (): Promise<ArchivedStrategy[]> => {
  const response = await api.get('/strategies/archived')
  return response.data
}

export const sanitizeStrategies = async (): Promise<{ rows_fixed: number }> => {
  const response = await api.post('/sanitize-strategies')
  return response.data
}

export const migrateDeletedToArchived = async (): Promise<{
  migrated_strategies: string[]
  migrated_bets: number
}> => {
  const response = await api.post('/migrate-deleted-to-archived')
  return response.data
}

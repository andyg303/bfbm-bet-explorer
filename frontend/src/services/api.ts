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

export const uploadBetsCSV = async (
  file: File,
  onProgress?: (pct: number) => void
): Promise<{ filename: string; inserted: number; updated: number; skipped: number; total_bets_in_db: number }> => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await axios.post(`${API_BASE_URL}/ingest`, formData, {
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return response.data
}

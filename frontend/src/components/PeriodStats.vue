<script setup lang="ts">
import { computed } from 'vue'
import { useBetStore } from '../stores/betStore'
import type { SummaryStats } from '../services/api'

const betStore = useBetStore()

type PeriodKey = 'yesterday' | 'last_7_days' | 'last_30_days' | 'previous_30_days'

const PERIODS: { key: PeriodKey; label: string; hint: string }[] = [
  { key: 'yesterday', label: 'Yesterday', hint: 'Bets started yesterday' },
  { key: 'last_7_days', label: 'Last 7 Days', hint: 'The 7 days up to and including yesterday' },
  { key: 'last_30_days', label: 'Last 30 Days', hint: 'The 30 days up to and including yesterday' },
  { key: 'previous_30_days', label: 'Previous 30 Days', hint: 'Days 31 to 60 back — does not overlap Last 30 Days' },
]

const ZERO: SummaryStats = {
  num_bets: 0, num_wins: 0, win_rate: 0,
  gross_pl: 0, commission_paid: 0, net_pl: 0, total_pl: 0,
  total_staked: 0, roi: 0, yield_pct: 0, num_strategies: 0,
}

const stats = computed(() => betStore.periodStats)

const fmtInt = (n: number) => (n || 0).toLocaleString()
const fmtMoney = (n: number) =>
  `${n >= 0 ? '+' : ''}${(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const fmtPct = (n: number) => `${(n || 0).toFixed(2)}%`
const plClass = (n: number) => (n >= 0 ? 'text-emerald-400' : 'text-rose-400')
const neutral = 'text-gray-900 dark:text-white'

interface Metric { label: string; value: string; cls: string }

function metricsFor(key: PeriodKey): Metric[] {
  const s: SummaryStats = stats.value?.[key] ?? ZERO
  const gross = s.gross_pl ?? s.total_pl ?? 0
  const net = s.net_pl ?? s.total_pl ?? 0
  return [
    { label: 'Bets', value: fmtInt(s.num_bets), cls: neutral },
    { label: 'Wins', value: fmtInt(s.num_wins), cls: neutral },
    { label: 'SR', value: fmtPct(s.win_rate), cls: 'text-teal-500 dark:text-teal-400' },
    { label: 'Gross', value: fmtMoney(gross), cls: plClass(gross) },
    { label: 'Comm', value: (s.commission_paid || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }), cls: 'text-amber-500' },
    { label: 'Net', value: fmtMoney(net), cls: plClass(net) },
    { label: 'Staked', value: (s.total_staked || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }), cls: neutral },
    { label: 'ROI', value: fmtPct(s.roi), cls: plClass(s.roi || 0) },
    { label: 'Strats', value: fmtInt(s.num_strategies), cls: 'text-amber-500' },
  ]
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
    <div v-for="p in PERIODS" :key="p.key" class="stat-card !p-3" :title="p.hint">
      <div class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">{{ p.label }}</div>
      <dl class="grid grid-cols-3 gap-x-2 gap-y-1.5">
        <div v-for="m in metricsFor(p.key)" :key="m.label">
          <dt class="text-[9px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">{{ m.label }}</dt>
          <dd class="text-xs font-mono font-semibold leading-tight truncate" :class="m.cls">{{ m.value }}</dd>
        </div>
      </dl>
    </div>
  </div>
</template>

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const periodStats = readFileSync(new URL('../src/components/PeriodStats.vue', import.meta.url), 'utf8')
const betStore = readFileSync(new URL('../src/stores/betStore.ts', import.meta.url), 'utf8')
const api = readFileSync(new URL('../src/services/api.ts', import.meta.url), 'utf8')
const appVue = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')

test('period stats row renders the four date buckets', () => {
  for (const label of ['Today', 'Yesterday', 'Last 7 Days', 'Last 30 Days']) {
    assert.match(periodStats, new RegExp(`label: '${label}'`), `missing period tile: ${label}`)
  }
  assert.match(periodStats, /xl:grid-cols-4/, 'tiles should span the full page width on desktop')
})

test('each tile shows the same figures as the main summary squares', () => {
  for (const label of ['Bets', 'Wins', 'SR', 'Gross', 'Comm', 'Net', 'Staked', 'ROI', 'Strats']) {
    assert.match(periodStats, new RegExp(`label: '${label}'`), `missing metric: ${label}`)
  }
})

test('period stats are fetched via the api client and stored', () => {
  assert.match(api, /api\.post\('\/period-stats'/, 'api.ts should call /period-stats')
  assert.match(betStore, /periodStats = ref<PeriodStats \| null>/, 'store should hold period stats')
  assert.match(betStore, /loadPeriodStats/, 'store should load period stats')
  assert.match(betStore, /withLoading\('periods'/, 'periods should have a loading section')
})

test('dashboard renders period tiles under the summary header', () => {
  const summaryIdx = appVue.indexOf('<SummaryHeader />')
  const periodIdx = appVue.indexOf('<PeriodStats />')
  assert.ok(summaryIdx >= 0, 'SummaryHeader should be rendered')
  assert.ok(periodIdx > summaryIdx, 'PeriodStats should render underneath the main squares')
})

test('period stats refresh alongside the other dashboard sections', () => {
  const refresh = betStore.match(/async function refreshAll[\s\S]*?\]\)/)
  assert.ok(refresh, 'refreshAll should exist')
  assert.match(refresh[0], /loadPeriodStats\(\)/, 'refreshAll should reload period stats')
})

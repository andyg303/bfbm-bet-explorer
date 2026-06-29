import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const appVue = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const betStore = readFileSync(new URL('../src/stores/betStore.ts', import.meta.url), 'utf8')

function loadDashboardDataBody() {
  const match = appVue.match(/async function loadDashboardData\(\) \{([\s\S]*?)\n\}\n\nonMounted/)
  assert.ok(match, 'loadDashboardData function should exist')
  return match[1]
}

test('dashboard paints summary before slower section refreshes finish', () => {
  const body = loadDashboardDataBody()

  assert.match(body, /await betStore\.loadSummaryStats\(\)/, 'initial dashboard load should await summary stats for first paint')
  assert.doesNotMatch(body, /await betStore\.refreshAll\(\)/, 'initial dashboard load should not block first paint on refreshAll')
  assert.ok(
    body.indexOf('await betStore.loadSummaryStats()') < body.indexOf('initialDashboardLoading.value = false'),
    'initial dashboard overlay should close after summary stats are available'
  )
})

test('dashboard sections are wrapped with section loading states', () => {
  assert.match(appVue, /import SectionLoading from '\.\/components\/SectionLoading\.vue'/)

  for (const section of ['summary', 'filters', 'strategies', 'plGraph', 'monthly', 'oddsBands', 'bets', 'archive']) {
    assert.match(appVue, new RegExp(`betStore\\.loadingSections\\.${section}`), `${section} should be wired to a section loader`)
  }
})

test('bet store tracks per-section dashboard loading flags', () => {
  assert.match(betStore, /const loadingSections = ref/, 'store should expose per-section loading flags')

  for (const section of ['filters', 'summary', 'strategies', 'bets', 'plGraph', 'monthly', 'oddsBands', 'archive', 'mergeSuggestions']) {
    assert.match(betStore, new RegExp(`${section}: false`), `${section} loading flag should have a default`)
  }

  for (const section of ['filters', 'summary', 'strategies', 'bets', 'plGraph', 'monthly', 'oddsBands']) {
    assert.match(betStore, new RegExp(`withLoading\\('${section}'`), `${section} loader should set its section loading flag`)
  }
})

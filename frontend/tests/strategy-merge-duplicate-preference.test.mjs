import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const strategyManager = readFileSync(new URL('../src/components/StrategyManager.vue', import.meta.url), 'utf8')

test('duplicate review can favour one original strategy across groups', () => {
  assert.match(strategyManager, /const preferredOriginalStrategy = ref<string \| null>\(null\)/, 'review should track the favoured original strategy')
  assert.match(strategyManager, /function duplicateOriginalStrategyOptions\(\)/, 'review should list original strategy options')
  assert.match(strategyManager, /function applyOriginalStrategyPreference\(strategy: string\)/, 'review should apply a chosen original strategy')
  assert.match(strategyManager, /preferredBet = group\.bets\.find\(bet => bet\.original_strategy === strategy\)/, 'preference should keep the chosen strategy row where present')
  assert.match(strategyManager, /for \(const bet of group\.bets\)/, 'preference should update all rows in matching groups')
})

test('duplicate review renders one checkbox per original strategy option', () => {
  assert.match(strategyManager, /Prefer original strategy/, 'review should label the preference controls')
  assert.match(strategyManager, /v-for="option in duplicateOriginalStrategyOptions\(\)"/, 'review should render every strategy option')
  assert.match(strategyManager, /type="checkbox"/, 'strategy preference controls should be checkboxes')
  assert.match(strategyManager, /:checked="preferredOriginalStrategy === option\.strategy"/, 'active strategy should be visibly checked')
  assert.match(strategyManager, /@change="applyOriginalStrategyPreference\(option\.strategy\)"/, 'checking an option should apply it')
})

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const strategyStats = readFileSync(new URL('../src/components/StrategyStats.vue', import.meta.url), 'utf8')
const strategyFilters = readFileSync(new URL('../src/components/StrategyFilters.vue', import.meta.url), 'utf8')
const betStore = readFileSync(new URL('../src/stores/betStore.ts', import.meta.url), 'utf8')
const api = readFileSync(new URL('../src/services/api.ts', import.meta.url), 'utf8')
const appVue = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')

test('strategy table exposes a Gmail-style star toggle per row', () => {
  assert.match(strategyStats, /toggleStar\(stat\.strategy\)/, 'each row should render a star toggle button')
  assert.match(strategyStats, /betStore\.starredStrategies\.has/, 'star fill state should come from the store')
  assert.match(strategyStats, /title="Remove star"|'Remove star'/, 'starred rows should expose an unstar tooltip')
})

test('add-to-group button only activates when more than one strategy is ticked', () => {
  assert.match(strategyStats, /Add to Group \(/, 'bulk group button should be labelled')
  assert.match(strategyStats, /:disabled="selectedStrategies\.size < 2"/, 'button stays disabled until 2+ selections')
  assert.match(strategyStats, /betStore\.strategyGroups/, 'menu should list existing groups')
  assert.match(strategyStats, /v-model="newGroupName"/, 'menu should offer creating a new group')
  assert.match(strategyStats, /createGroupAndAddSelection/, 'create path should also add the selection')
})

test('starred is offered as a pseudo-group inside the same group filter', () => {
  assert.match(strategyFilters, /value="starred"/, 'group select should include a Starred option')
  assert.match(strategyFilters, /`group:\$\{group\.id\}`/, 'group select should list named groups')
  assert.match(strategyFilters, /betStore\.applyGroupFilter/, 'changing the select should apply the filter')
})

test('bet store resolves group filters into the strategies filter', () => {
  assert.match(betStore, /starredStrategies = ref<Set<string>>/, 'store should track starred strategy names')
  assert.match(betStore, /strategyGroups = ref<StrategyGroup\[\]>/, 'store should track groups')
  assert.match(betStore, /strategyGroupFilter = ref\(''\)/, 'store should track the active group filter')
  assert.match(betStore, /resolveGroupFilterStrategies/, 'store should resolve a filter to member names')
  assert.match(betStore, /EMPTY_GROUP_SENTINEL/, 'empty groups must filter to zero strategies, not all')
})

test('api client exposes star and group endpoints', () => {
  for (const pattern of [
    /api\.get\('\/strategies\/meta'\)/,
    /api\.post\('\/strategies\/star'/,
    /api\.post\('\/strategy-groups'/,
    /api\.post\(`\/strategy-groups\/\$\{groupId\}\/members`/,
    /api\.delete\(`\/strategy-groups\/\$\{groupId\}\/members`/,
    /api\.delete\(`\/strategy-groups\/\$\{groupId\}`\)/,
  ]) {
    assert.match(api, pattern, `api.ts missing ${pattern}`)
  }
})

test('dashboard load fetches star/group metadata', () => {
  assert.match(appVue, /betStore\.loadStrategyMeta\(\)/, 'dashboard should load strategy metadata')
})

test('merging strategies refreshes stars and groups', () => {
  const mergeBlock = betStore.match(/async function mergeStrategies[\s\S]*?finally/)
  assert.ok(mergeBlock, 'mergeStrategies should exist')
  assert.match(mergeBlock[0], /loadStrategyMeta/, 'merge should reload star/group metadata')
})

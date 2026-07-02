import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const confirmDialog = readFileSync(new URL('../src/components/ConfirmDialog.vue', import.meta.url), 'utf8')
const strategyManager = readFileSync(new URL('../src/components/StrategyManager.vue', import.meta.url), 'utf8')

test('confirm dialog exposes loading feedback and blocks duplicate actions', () => {
  assert.match(confirmDialog, /loading\?: boolean/, 'dialog should accept a loading prop')
  assert.match(confirmDialog, /loadingLabel\?: string/, 'dialog should accept loading text')
  assert.match(confirmDialog, /role="progressbar"/, 'dialog should render an indeterminate progress bar while loading')
  assert.match(confirmDialog, /:disabled="loading"/, 'dialog actions should be disabled while loading')
  assert.match(confirmDialog, /animate-spin/, 'confirm button should show a spinner while loading')
})

test('strategy merge confirmation passes merge loading state into dialogs', () => {
  assert.match(strategyManager, /const suggestionMergeLoading = ref\(false\)/, 'suggestion merge should track local loading state')
  assert.match(strategyManager, /suggestionMergeLoading\.value = true/, 'suggestion merge should set loading immediately on confirm')
  assert.match(strategyManager, /suggestionMergeLoading\.value = false/, 'suggestion merge should clear loading after completion')
  assert.match(strategyManager, /:loading="suggestionMergeLoading"/, 'suggestion dialog should receive loading state')
  assert.match(strategyManager, /:loading="manualLoading"/, 'manual dialog should receive loading state')
  assert.match(strategyManager, /loading-label="Merging strategies"/, 'merge dialogs should label the in-progress state')
})

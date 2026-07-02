# Strategy Merge Duplicate Deletion Design

## Goal

Add an opt-in destructive duplicate cleanup to strategy merges so users can merge strategies that contain overlapping bets without leaving duplicate records in the target strategy.

## Current Behavior

The existing `/strategies/merge` endpoint renames every non-deleted bet in the selected source strategies to the target strategy. It does not inspect, merge, soft-delete, or hard-delete duplicate bets. If the same bet appears in multiple source strategies, those rows remain after merge with the same target strategy name.

## Proposed Behavior

Keep the existing merge behavior as the default. Add a `delete_duplicates` boolean to the merge request. When it is false or omitted, the endpoint behaves as it does today.

When `delete_duplicates` is true:

- First rename source strategy bets into the target strategy.
- Then inspect the authenticated user's non-deleted, non-archived bets in the target strategy.
- Group duplicates by the same bet name and same market.
- Keep exactly one bet in each duplicate group.
- Delete every later duplicate in that group.

The bet to keep is selected by earliest timestamp using this order:

1. `placed_date`
2. `matched_date`
3. `settled_date`
4. `start_time`
5. lowest database `id` as the final tie-breaker

Odds, stake, P/L, status, and price fields are intentionally ignored when detecting duplicates.

## Duplicate Key

Use the bet `description` as the bet name source because existing imported BFBM data maps both `Description` and `Name` into this field. For market identity, prefer `market_id` when present, then fall back to `market_name`, then the market portion of `description` before the final selection segment.

Only records with enough information to form both sides of the key should be considered for deletion. Bets with missing bet name or missing market identity should not be deleted as duplicates.

## Backend Contract

Extend `MergeStrategiesRequest` with:

```python
delete_duplicates: bool = False
```

Extend the merge response with:

```json
{
  "ok": true,
  "merged_bets": 12,
  "deleted_duplicates": 3,
  "source_strategies": ["Old Name"],
  "target_strategy": "Target Name"
}
```

Duplicate deletion must stay scoped to the authenticated user's target strategy and must not affect other users, archived bets, or already deleted bets.

## Frontend Behavior

Add a checkbox to both merge entry points:

- Auto-suggestion merge detail panel.
- Manual merge controls.

Checkbox label:

```text
Delete duplicate bets after merge
```

Help text:

```text
Destructive and cannot be undone. Keeps the first duplicate by placed date, then matched date, settled date, start time, and database ID; deletes later duplicates with the same bet name and market. Odds are ignored.
```

If checked, the confirmation dialog should explicitly mention duplicate deletion. Success toasts should include both the merged bet count and deleted duplicate count.

## Testing

Backend tests should cover:

- Default merge still renames strategies and deletes no duplicates.
- Opt-in duplicate deletion keeps the earliest duplicate by `placed_date`.
- Timestamp fallback order handles missing `placed_date`.
- Equal timestamps keep the lowest database `id`.
- Other users' duplicate-looking bets are not touched.
- Archived and already deleted bets are not considered for deletion.

Frontend tests are not required unless the project already has a practical component test setup for this component. Type checking/build verification is sufficient for the UI wiring.

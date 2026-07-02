# Strategy Merge Duplicate Deletion Design

## Goal

Add an opt-in destructive duplicate cleanup to strategy merges so users can merge strategies that contain overlapping bets without leaving duplicate records in the target strategy.

## Current Behavior

The existing `/strategies/merge` endpoint renames every non-deleted bet in the selected source strategies to the target strategy. It does not inspect, merge, soft-delete, or hard-delete duplicate bets. If the same bet appears in multiple source strategies, those rows remain after merge with the same target strategy name.

## Proposed Behavior

Keep the merge itself non-destructive. After source strategy bets are renamed into the target strategy, inspect the authenticated user's non-deleted, non-archived bets in the target strategy and return duplicate groups for review.

Each duplicate group should include:

- the shared bet name and market
- every duplicate bet in the group
- relevant comparison fields, including event, timestamps, odds, type, status, and original strategy where it can be captured during the merge
- a suggested keep bet
- suggested delete bet IDs

The UI should auto-select the suggested delete rows, but the user can change the selection before deleting anything. The user can also keep all duplicates.

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

Extend the merge response with:

```json
{
  "ok": true,
  "merged_bets": 12,
  "duplicate_groups": [
    {
      "bet_name": "Runner",
      "market": "Market One",
      "suggested_keep_bet_id": 10,
      "suggested_delete_bet_ids": [11],
      "bets": [
        {
          "id": 10,
          "bet_name": "Runner",
          "market": "Market One",
          "event": "Event One",
          "original_strategy": "Target",
          "placed_date": "2026-01-01T12:00:00",
          "avg_price_matched": 2.0
        }
      ]
    }
  ],
  "source_strategies": ["Old Name"],
  "target_strategy": "Target Name"
}
```

Add a separate confirmation endpoint that accepts the target strategy and selected bet IDs. It must hard-delete only selected rows that still belong to duplicate groups for the authenticated user's target strategy. It must reject requests that would delete every bet in a duplicate group.

Duplicate review and deletion must stay scoped to the authenticated user's target strategy and must not affect other users, archived bets, or already deleted bets.

## Frontend Behavior

After a merge completes, if duplicate groups are returned, show a grouped duplicate review table. Each group should make it clear which rows are duplicates of each other and should include bet name, market, event, original strategy, placed/matched/settled/start timestamps, odds, type, and status.

Auto-select the suggested delete rows. The user can change row selection, but the UI should keep at least one row unselected in each group. Provide two actions:

- Keep duplicates
- Delete selected duplicates

No duplicate deletion checkbox is shown before merge.

## Testing

Backend tests should cover:

- Merge still renames strategies and deletes no duplicates.
- Merge returns duplicate review groups with suggested delete IDs.
- Timestamp fallback order handles missing `placed_date`.
- Equal timestamps keep the lowest database `id`.
- Other users' duplicate-looking bets are not included.
- Archived and already deleted bets are not considered.
- Confirmed deletion hard-deletes only selected duplicate rows.
- Confirmed deletion rejects attempts to delete every bet in a group.

Frontend tests are not required unless the project already has a practical component test setup for this component. Type checking/build verification is sufficient for the UI wiring.

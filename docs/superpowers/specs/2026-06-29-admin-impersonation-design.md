# Admin Impersonation Design

## Goal

Allow an admin to view a user's dashboard exactly as that user sees it for debugging, while guaranteeing the impersonated session is read-only.

## Approved Approach

Use a temporary JWT access token for impersonation. An admin starts from the existing admin users table, clicks a "View as" action for a non-admin user, and the backend returns a short-lived access token for the target user. The token includes claims that identify the original admin and mark the session as read-only.

The frontend temporarily stores the admin's current token/profile separately, replaces the active auth token/profile with the impersonation token/profile, and navigates to the normal dashboard. Because the dashboard keeps using the existing API calls, all user-scoped reads reuse the existing `get_current_user` and `apply_filters(..., user.id)` architecture.

## Read-Only Enforcement

The backend must reject mutating actions when the current JWT contains a read-only impersonation claim. This protection is required even if someone manually calls the API.

Read-only impersonation blocks:

- CSV upload and automation ingest through the web session
- bet deletion
- strategy archive, restore, delete, merge, migrate, and sanitize actions
- commission recalculation and commission settings updates
- account profile, password, Stripe portal/checkout, automation token, and referral actions

Read-only impersonation allows:

- dashboard reads such as filters, strategy stats, bets, charts, monthly P/L, summaries, archived strategy reads, strategy lists, merge suggestions, upload history, and auth/me

## Frontend Experience

While impersonating, show a persistent banner on the dashboard that names the target user and provides a "Return to admin" action. The banner is a safety signal and the restore path for the admin's real session.

Hide or disable dashboard controls that would mutate user data while impersonating. The backend remains the final enforcement point.

## Security Notes

Impersonation tokens are access-only and short-lived. They do not include or issue a refresh token, so the session cannot silently extend itself. Admin users cannot impersonate other admin users or inactive users.

No password is needed and no password hash is shared. The original admin identity is kept in the token for server-side checks and future auditability.

## Testing

Backend tests cover token claim parsing, the admin-only impersonation endpoint, and read-only rejection for at least one representative mutating endpoint. Frontend verification covers TypeScript compilation and production build.

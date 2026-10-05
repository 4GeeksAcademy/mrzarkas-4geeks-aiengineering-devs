# HealthCore Management backoffice

Static development UI for reading catalogues, synthetic master data and
authorized Management audit events. Serve the `uis/backoffice/management`
directory with any static server, then enter the API URL and a JWT issued for
development. It never persists the token and backend authorization remains the
security boundary.

This is intentionally read-only in M6. Administrative mutations remain
available through the protected API while the final UX and M0 approvals are
pending.

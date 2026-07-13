# PR Response Doc - CineLog Watchlist Feature

## Comment 1 — Rename
**What I did:**
Renamed `save_to_watchlist()` to `add_to_watchlist()` in
`services/watchlist_service.py` and updated the one call site in
`routes/watchlist/watchlist.py` (the import line and the call inside
`add_film()`). Also updated the docstring first line to match.
The rename follows the project's `verb_to_noun` naming convention
already established by `add_to_collection()` in `collection_service.py`.

**How I verified:**
Searched the entire codebase for `save_to_watchlist` — found exactly
two references (the definition and the call site), both updated.
No other files imported or called the old name.
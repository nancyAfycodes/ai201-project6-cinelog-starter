# PR Response Doc — CineLog Watchlist Feature

## AI Usage
Used AI tools to understand existing codebase patterns before making
changes (add_to_collection, test structure). Used AI to verify code
changes and stress-test design arguments for Comments 4 and 5.
All design decisions and written responses are my own reasoning.

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

## Comment 2 — Deduplication
**What I did:**
Added an `AlreadyInWatchlistError` exception class to
`watchlist_service.py` and a deduplication guard inside
`add_to_watchlist()`, between the film-exists check and the entry
creation. The guard queries for an existing `WatchlistEntry` with the
same `(user_id, film_id)` pair and raises `AlreadyInWatchlistError`
if one is found.

Defined the exception in `watchlist_service.py` directly rather than
in `collection_service.py` — it belongs to the watchlist feature, not
the collection feature.

**How I verified:**
Followed the same pattern as `add_to_collection()` in
`collection_service.py` step for step: film check first, dedup check
second, create only if both pass. The dedup test
`test_add_to_watchlist_duplicate_raises` confirms the guard fires and
no duplicate row is created.

## Comment 3 — Missing test
**What I did:**
Created `tests/test_watchlist.py` with three tests:
- `test_add_to_watchlist_creates_entry` — happy path, verifies the entry
  is returned and persisted in the DB
- `test_add_to_watchlist_duplicate_raises` — verifies `AlreadyInWatchlistError`
  fires on a duplicate add and that only one row exists after
- `test_add_to_watchlist_nonexistent_film_raises` — verifies
  `FilmNotFoundError` fires when the film_id doesn't exist in the DB

**How I verified:**
Modeled each test directly on its equivalent in `test_collection.py`.
Removed the sort order test for now since `get_watchlist()` sorts
alphabetically by title, not by date — that behavior is under discussion
in Comment 5. Ran `pytest tests/test_watchlist.py -v` to confirm all
three pass.

## Comment 4 — Default visibility
**My position:**
Keep `public=True` as the default.

**Reasoning:**
The public default supports CineLog's community value of sharing, as it
allows users to see what films others have on their watchlist, which
encourages discovery. Keeping it public by default lowers the barrier
to that shared experience without requiring users to actively opt in.

**Tradeoff acknowledged:**
Some users may prefer privacy for films covering sensitive topics. This
could be mitigated by an opt-out feature at the individual film level,
allowing users to mark specific titles as private while keeping the
default public.

## Comment 5 — Sort order
**My position:**
Keep the current alphabetical sort order.

**Reasoning:**
As a watchlist grows, date-added order buries older films at the bottom,
making it harder to find a specific title by name. If users aren't
consistently removing films after watching them, the list becomes
cluttered and date-added order compounds that problem making it difficult to search for films. 
Therefore, alphabetical order stays stable and scannable regardless of list size.

**Engagement with reviewer's point:**
The reviewer's preference for date-added is valid — it surfaces recently
added films immediately. However, alphabetical order serves long-term
usability better as the list grows. A possible tradeoff would be an
auto-remove feature that removes films from the watchlist once watched
— which would make date-added order more practical and address the
reviewer's preference directly.

## Comment 6 — Rebase
**What conflicted:**
The refactor on `main` migrated `Film.id` from `db.Integer` to
`db.String(36)` (UUID). My branch still had `WatchlistEntry.film_id`
typed as `db.Integer`. Additionally, because `WatchlistEntry` didn't
exist on `main`, Git took `main`'s version of `models.py` wholesale
during the rebase, dropping `WatchlistEntry` entirely.

**How I resolved it:**
Ran `git rebase origin/main`. After the rebase completed, confirmed
`models.py` was missing `WatchlistEntry`. Manually restored the class
with `film_id` typed as `db.String(36)` to match the UUID refactor.
Also updated the `film_id` docstring in `watchlist_service.py` from
`(int)` to `(str): UUID of the film.`

**How I verified no conflict remains:**
Ran `git show HEAD:models.py` to confirm `WatchlistEntry` was restored
with `film_id = db.Column(db.String(36), ...)`. Ran `git log --oneline`
to confirm linear history with no merge commits. The refactor commit
`07ca580` appears in the branch history below my commits.

## PR Description
CineLog Watchlist Feature — adds the ability for users to save films
they intend to watch. Includes:
- `WatchlistEntry` model with `public` visibility flag
- `add_to_watchlist()` and `get_watchlist()` service functions
- Deduplication guard following the same pattern as `add_to_collection()`
- Tests for happy path, duplicate, and nonexistent film cases
- Rebased on main after UUID film ID refactor

Design decisions: default visibility is `public=True` to support
community sharing (opt-out mitigates privacy concerns). Sort order
kept alphabetical for long-term list navigability.

## Git Log image
![Git log showing conventional commits](git-log.png)
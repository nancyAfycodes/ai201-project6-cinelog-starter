"""
tests/test_watchlist.py — CineLog

Tests for the watchlist service.
These tests demonstrate the patterns used across the codebase — read them
before writing your own tests for the watchlist feature (see Comment 4).
"""

import pytest
from app import create_app, db
from models import User, Film, WatchlistEntry
from services.watchlist_service import (
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
    FilmNotFoundError,
    AlreadyInWatchlistError,
    NotInWatchlistError,
)


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """A user to use in tests."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_film(app):
    """A film to use in tests."""
    with app.app_context():
        film = Film(title="Paddington 2", year=2017, genre="Comedy")
        db.session.add(film)
        db.session.commit()
        return film.id


# ── Basic add ───────────────────────────────────────────────────────────────

def test_add_to_watchlist_creates_entry(app, sample_user, sample_film):
    """
    Adding a valid film should create a WatchlistEntry in the database.
    """
    with app.app_context():
        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film)

        assert entry is not None
        assert entry.user_id == sample_user
        assert entry.film_id == sample_film

        # Verify it persisted
        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db is not None


# ── Deduplication ────────────────────────────────────────────────────────────

def test_add_to_watchlist_duplicate_raises(app, sample_user, sample_film):
    """
    Adding the same film twice should raise AlreadyInWatchlistError,
    not silently create a duplicate entry.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        with pytest.raises(AlreadyInWatchlistError):
            add_to_watchlist(user_id=sample_user, film_id=sample_film)

        # Confirm only one entry exists
        count = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).count()
        assert count == 1


# ── Nonexistent film ─────────────────────────────────────────────────────────

def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that doesn't exist in the database should raise
    FilmNotFoundError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)

# ── Remove film from watchlist ─────────────────────────────────────────────────────────

def test_remove_from_watchlist_not_in_watchlist_raises(app, sample_user):
    """
    Removing a film_id that is not in the user's watchlist should raise
    NotInWatchlistError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NotInWatchlistError):
            remove_from_watchlist(user_id=sample_user, film_id=fake_film_id)


def test_remove_from_watchlist_removes_entry(app, sample_user, sample_film):
    """
    Removing a film that is on the watchlist should delete the entry
    from the database and return True.
    """
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)
        result = remove_from_watchlist(user_id=sample_user, film_id=sample_film)

        assert result is True

        # Verify it was removed from the DB
        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db is None

# ── Result format for watchlist ─────────────────────────────────────────────────────────

def test_get_watchlist_returns_correct_format(app, sample_user, sample_film):
    """
    get_watchlist() should return a list of dicts, each containing
    film data merged with watchlist metadata (date_added, public).
    """
    with app.app_context():
        # Arrange — add a film to the watchlist
        add_to_watchlist(user_id=sample_user, film_id=sample_film)

        # Act
        result = get_watchlist(user_id=sample_user)

        # Assert — result is a list with one item
        assert isinstance(result, list)
        assert len(result) == 1

        # Assert — the item is a dict with the expected keys
        film = result[0]
        assert "title" in film  # title key exists
        assert "date_added" in film  # date_added key exists
        assert "public" in film # public key exists

# ── Toggle Visibility ─────────────────────────────────────────────────────────

def test_add_to_watchlist_with_public_false(app, sample_user, sample_film):
    """
    Adding a film with public=False should create an entry with public=False.
    """
    with app.app_context():
        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film, public=False)

        assert entry.public is False

        # Verify it persisted with public=False
        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert in_db.public is False


def test_add_to_watchlist_defaults_to_public_true(app, sample_user, sample_film):
    """
    Adding a film without specifying public should default to public=True.
    """
    with app.app_context():
        entry = add_to_watchlist(user_id=sample_user, film_id=sample_film)

        assert entry.public is True
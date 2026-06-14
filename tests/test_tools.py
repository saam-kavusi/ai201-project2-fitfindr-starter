"""
test_tools.py

Unit tests for the three FitFindr tools, run individually before they are
wired into the agent loop.

These tests call the real functions (no mocking). The LLM-backed tools
(suggest_outfit, create_fit_card) catch all exceptions internally and always
return a non-empty string, so the string assertions hold whether or not a live
GROQ_API_KEY is configured.

Run with:
    pytest tests/test_tools.py -v
"""

import pytest

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def test_search_returns_results():
    """Happy path: a common query under a generous cap returns a non-empty
    list of dicts."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(item, dict) for item in results)


def test_search_empty_results():
    """Failure mode: an impossible query matches nothing and returns []."""
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    """The max_price filter is respected: every item costs <= 50."""
    results = search_listings("jacket", size=None, max_price=50)

    assert all(item["price"] <= 50 for item in results)


def test_search_empty_description():
    """Edge case: an empty description has no search terms, so nothing
    matches and [] is returned."""
    results = search_listings("", size=None, max_price=None)

    assert results == []


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def test_suggest_outfit_with_example_wardrobe():
    """Happy path: a real search result paired with a populated wardrobe
    produces a non-empty string."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    if not results:
        pytest.skip("No listings matched; cannot test suggest_outfit.")

    new_item = results[0]
    wardrobe = get_example_wardrobe()

    suggestion = suggest_outfit(new_item, wardrobe)

    assert isinstance(suggestion, str)
    assert suggestion.strip() != ""


def test_suggest_outfit_with_empty_wardrobe():
    """An empty wardrobe is handled gracefully: still returns a non-empty
    string (general styling advice) instead of raising."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    if not results:
        pytest.skip("No listings matched; cannot test suggest_outfit.")

    new_item = results[0]
    wardrobe = get_empty_wardrobe()

    suggestion = suggest_outfit(new_item, wardrobe)

    assert isinstance(suggestion, str)
    assert suggestion.strip() != ""


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def test_create_fit_card_returns_caption():
    """Happy path: a valid outfit and item produce a non-empty caption."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    if not results:
        pytest.skip("No listings matched; cannot test create_fit_card.")

    new_item = results[0]
    outfit = (
        "Pair the vintage graphic tee with high-waisted blue jeans, white "
        "sneakers, and a denim jacket for an easy everyday look."
    )

    caption = create_fit_card(outfit, new_item)

    assert isinstance(caption, str)
    assert caption.strip() != ""
    assert "could not be created" not in caption.lower()


def test_create_fit_card_empty_outfit():
    """Failure mode: an empty outfit returns a descriptive error string
    (and never raises)."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    new_item = results[0] if results else {"title": "test item", "price": 10}

    caption = create_fit_card("", new_item)

    assert isinstance(caption, str)
    assert "could not be created" in caption


def test_create_fit_card_whitespace_outfit():
    """A whitespace-only outfit is treated as missing and returns the same
    descriptive error string."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    new_item = results[0] if results else {"title": "test item", "price": 10}

    caption = create_fit_card("   ", new_item)

    assert isinstance(caption, str)
    assert "could not be created" in caption

"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv(dotenv_path=".env")


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches.
    """
    listings = load_listings()

    if not description or not description.strip():
        return []

    stop_words = {
        "i", "im", "i'm", "am", "looking", "look", "for", "a", "an", "the",
        "and", "or", "with", "to", "under", "want", "need", "find", "me",
        "whats", "what", "out", "there", "how", "would", "style", "it"
    }

    query_lower = description.lower()
    query_words = {
        word for word in re.findall(r"\w+", query_lower)
        if word not in stop_words
    }

    if not query_words:
        return []

    # Per-field weights: a match in a structured field (style tags, title)
    # is a much stronger signal of what the item *is* than an incidental
    # mention buried in the free-text description (e.g. "great for layering
    # under a graphic tee"). Description matches still count, just for less.
    field_weights = {
        "style_tags": 5,
        "title": 4,
        "category": 3,
        "colors": 2,
        "brand": 2,
        "platform": 1,
        "description": 1,
    }

    matches = []

    for listing in listings:
        if max_price is not None and listing.get("price", 0) > max_price:
            continue

        if size is not None:
            if size.lower() not in str(listing.get("size", "")).lower():
                continue

        style_tags = listing.get("style_tags", [])
        fields = {
            "style_tags": " ".join(style_tags).lower(),
            "title": str(listing.get("title", "")).lower(),
            "category": str(listing.get("category", "")).lower(),
            "colors": " ".join(listing.get("colors", [])).lower(),
            "brand": str(listing.get("brand") or "").lower(),
            "platform": str(listing.get("platform", "")).lower(),
            "description": str(listing.get("description", "")).lower(),
        }

        # Score word overlap per field, scaled by that field's weight.
        score = 0
        for field, text in fields.items():
            field_words = set(re.findall(r"\w+", text))
            overlap = len(query_words & field_words)
            score += overlap * field_weights[field]

        # Strong bonus for an exact style-tag phrase match. Style tags may be
        # multi-word (e.g. "graphic tee", "band tee"); if such a tag appears
        # verbatim in the query, the listing genuinely *is* that style, so it
        # should outrank items that only name the phrase in their description.
        for tag in style_tags:
            if tag.lower() in query_lower:
                score += 10

        if score == 0:
            continue

        matches.append((score, listing))

    matches.sort(key=lambda pair: (-pair[0], pair[1].get("price", 0)))

    return [listing for _, listing in matches]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    
    try:
        client = _get_groq_client()

        wardrobe_items = wardrobe.get("items", []) if wardrobe else []

        item_title = new_item.get("title", "this item")
        item_category = new_item.get("category", "clothing")
        item_colors = ", ".join(new_item.get("colors", []))
        item_style_tags = ", ".join(new_item.get("style_tags", []))
        item_description = new_item.get("description", "")

        if not wardrobe_items:
            prompt = f"""
You are FitFindr, a secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Category: {item_category}
- Description: {item_description}
- Colors: {item_colors}
- Style tags: {item_style_tags}

The user's wardrobe is empty or not available.

Suggest one complete outfit using general clothing pieces that would pair well with this item.
Do not say you cannot help. Give practical styling advice.
Keep the response concise, specific, and casual.
"""
        else:
            formatted_wardrobe = []

            for item in wardrobe_items:
                name = item.get("name", "Unnamed item")
                category = item.get("category", "unknown category")
                colors = ", ".join(item.get("colors", []))
                style_tags = ", ".join(item.get("style_tags", []))

                formatted_wardrobe.append(
                    f"- {name} | category: {category} | colors: {colors} | style tags: {style_tags}"
                )

            wardrobe_text = "\n".join(formatted_wardrobe)

            prompt = f"""
You are FitFindr, a secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Category: {item_category}
- Description: {item_description}
- Colors: {item_colors}
- Style tags: {item_style_tags}

The user's wardrobe contains:
{wardrobe_text}

Suggest 1 complete outfit using the new thrifted item and specific pieces from the user's wardrobe.
Mention the new item by name.
Include practical styling details like fit, color balance, shoes, layers, or accessories.
Keep the response concise, specific, and casual.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful fashion assistant for secondhand clothing and outfit styling.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=250,
        )

        outfit = response.choices[0].message.content.strip()

        if not outfit:
            return (
                "I could not generate an outfit suggestion for this item. "
                "Try adding more wardrobe details or choosing a different listing."
            )

        return outfit

    except Exception as e:
        return (
            "I could not create an outfit suggestion right now. "
            f"Reason: {str(e)}"
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
   
    if not outfit or not outfit.strip():
        return (
            "Fit card could not be created because the outfit suggestion was "
            "missing or incomplete. Try generating the outfit again or choose another listing."
        )

    try:
        client = _get_groq_client()

        item_title = new_item.get("title", "this thrifted item")
        item_price = new_item.get("price", "unknown price")
        item_platform = new_item.get("platform", "a secondhand platform")
        item_condition = new_item.get("condition", "unknown condition")
        item_brand = new_item.get("brand") or "unbranded"
        item_colors = ", ".join(new_item.get("colors", []))
        item_style_tags = ", ".join(new_item.get("style_tags", []))

        prompt = f"""
You are FitFindr, a secondhand fashion styling assistant.

Create a short, shareable outfit caption for this thrifted item and outfit.

Thrifted item:
- Title: {item_title}
- Price: ${item_price}
- Platform: {item_platform}
- Condition: {item_condition}
- Brand: {item_brand}
- Colors: {item_colors}
- Style tags: {item_style_tags}

Outfit suggestion:
{outfit}

Write a 2-4 sentence caption that sounds like a real Instagram or TikTok outfit post.
Mention the item title, price, and platform naturally one time.
Make it casual, specific, and stylish.
Do not sound like a product listing.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You write casual, stylish secondhand outfit captions.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.9,
            max_tokens=180,
        )

        fit_card = response.choices[0].message.content.strip()

        if not fit_card:
            return (
                f"Thrifted {item_title} for ${item_price} on {item_platform}. "
                f"Styled with a look inspired by {item_style_tags or 'secondhand fashion'}."
            )

        return fit_card

    except Exception as e:
        return (
            f"Thrifted {new_item.get('title', 'this item')} and styled it into a complete fit. "
            f"Fit card fallback used because the caption generator failed: {str(e)}"
        )

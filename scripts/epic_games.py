"""Shared Epic Games giveaway parsing and IST expiry formatting.

Used by scripts/epic_alert.py and tests/test_epic_games.py.
"""

from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
EPIC_FREE_GAMES_URL = "https://store.epicgames.com/en-US/free-games"


def _parse_utc(value):
    """Parse an Epic ISO-8601 date, or return None when it is missing/invalid."""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def extract_free_games(data, now=None):
    """Return only actively free, promoted titles, with optional expiry dates."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    elements = (
        (data or {}).get("data", {})
        .get("Catalog", {})
        .get("searchStore", {})
        .get("elements", [])
    )
    games = []
    for game in elements:
        price = (game.get("price") or {}).get("totalPrice") or {}
        if price.get("discountPrice") != 0:
            continue

        promotions = (game.get("promotions") or {}).get("promotionalOffers") or []
        active_offers = []
        for group in promotions:
            for offer in group.get("promotionalOffers") or []:
                start = _parse_utc(offer.get("startDate"))
                end = _parse_utc(offer.get("endDate"))
                if start is not None and start <= now and (end is None or now < end):
                    active_offers.append(end)

        if not active_offers:
            continue

        slug = game.get("productSlug")
        if not slug:
            mappings = game.get("offerMappings") or []
            if mappings:
                slug = mappings[0].get("pageSlug")
        url = (
            f"https://store.epicgames.com/en-US/p/{slug}"
            if slug else EPIC_FREE_GAMES_URL
        )
        # If an active offer has an unknown end date, avoid inventing an expiry.
        known_end_dates = [end for end in active_offers if end is not None]
        expiry = min(known_end_dates) if known_end_dates and None not in active_offers else None
        games.append({
            "title": game["title"],
            "url": url,
            "expires_at": expiry,
        })

    return games


def format_expiry(expires_at):
    """Format an actual promotion expiry in India Standard Time."""
    if expires_at is None:
        return None
    if isinstance(expires_at, str):
        expires_at = _parse_utc(expires_at)
    if expires_at is None:
        return None
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    dt = expires_at.astimezone(IST)
    hour = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{dt:%A}, {dt.day} {dt:%b %Y}, {hour}:{dt.minute:02d} {ampm} IST"

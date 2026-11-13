import unittest
from datetime import datetime, timezone

from scripts.epic_games import extract_free_games, format_expiry


class EpicGamesTests(unittest.TestCase):
    NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)

    def game_data(self, start, end, price=0):
        return {
            "data": {
                "Catalog": {
                    "searchStore": {
                        "elements": [{
                            "title": "Sample Game",
                            "productSlug": "sample-game",
                            "price": {"totalPrice": {"discountPrice": price}},
                            "promotions": {"promotionalOffers": [{
                                "promotionalOffers": [{
                                    "startDate": start,
                                    "endDate": end,
                                }],
                            }]},
                        }],
                    },
                },
            },
        }

    def test_active_giveaway_formats_ist_expiry(self):
        data = self.game_data(
            "2026-11-12T00:00:00.000Z", "2026-11-19T15:00:00.000Z"
        )
        games = extract_free_games(data, now=self.NOW)
        self.assertEqual(len(games), 1)
        self.assertEqual(
            format_expiry(games[0]["expires_at"]),
            "Thursday, 19 Nov 2026, 8:30 PM IST",
        )

    def test_expired_giveaway_is_excluded(self):
        data = self.game_data("2026-11-11T00:00:00Z", "2026-11-12T00:00:00Z")
        self.assertEqual(extract_free_games(data, now=self.NOW), [])

    def test_upcoming_giveaway_is_excluded(self):
        data = self.game_data("2026-11-14T00:00:00Z", "2026-11-20T00:00:00Z")
        self.assertEqual(extract_free_games(data, now=self.NOW), [])

    def test_paid_game_is_excluded(self):
        data = self.game_data("2026-11-12T00:00:00Z", "2026-11-20T00:00:00Z", 299)
        self.assertEqual(extract_free_games(data, now=self.NOW), [])

    def test_unknown_expiry_is_not_invented(self):
        data = self.game_data("2026-11-12T00:00:00Z", None)
        games = extract_free_games(data, now=self.NOW)
        self.assertEqual(len(games), 1)
        self.assertIsNone(format_expiry(games[0]["expires_at"]))


if __name__ == "__main__":
    unittest.main()

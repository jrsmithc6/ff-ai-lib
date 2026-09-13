import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from ff_ai_lib.sleeper import SleeperClient, SleeperError, build_snapshot, validate_week
from ff_ai_lib.briefing import render_briefing


class SleeperTests(unittest.TestCase):
    def test_cache_retains_fetch_time_and_avoids_network(self):
        with tempfile.TemporaryDirectory() as directory:
            client = SleeperClient(directory)
            with patch("ff_ai_lib.sleeper.urlopen", return_value=io.BytesIO(b'{"42": {}}')) as fetch:
                self.assertEqual(client.players(), {"42": {}})
                timestamp = client.sources["players/nfl"]
                self.assertEqual(client.players(), {"42": {}})
                self.assertEqual(client.sources["players/nfl"], timestamp)
                self.assertEqual(fetch.call_count, 1)

    def test_expired_cache_is_not_silently_served(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "state_nfl.json").write_text(json.dumps({"fetched_at_epoch": 0, "fetched_at": "old", "data": {}}))
            with patch("ff_ai_lib.sleeper.urlopen", side_effect=URLError("offline")), patch("ff_ai_lib.sleeper.time.sleep"):
                with self.assertRaises(SleeperError):
                    SleeperClient(directory).state()

    def test_week_validation(self):
        for week in (0, 19, True, "1", None):
            with self.assertRaises(ValueError):
                validate_week(week)

    def test_snapshot_and_briefing_handle_empty_slot_and_unknown_player(self):
        records = {
            "league/123": {"sport": "nfl", "season": "2026", "name": "Test", "status": "in_season", "roster_positions": ["QB", "BN"], "settings": {}, "scoring_settings": {}},
            "state/nfl": {"season": "2026", "season_type": "regular", "week": 1},
            "league/123/users": [],
            "league/123/rosters": [{"roster_id": 1, "owner_id": None, "starters": ["0"], "players": ["999"], "reserve": None}],
            "league/123/matchups/1": [], "league/123/transactions/1": [],
            "league/123/traded_picks": [], "league/123/drafts": [], "players/nfl": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            client = SleeperClient(directory)
            with patch.object(client, "_get", side_effect=lambda path, **kw: records[path]):
                snapshot = build_snapshot(client, "123")
                briefing = render_briefing(snapshot)
                self.assertIn("EMPTY SLOT", briefing)
                self.assertIn("999 [999]", briefing)
                self.assertEqual(snapshot["teams"][0]["team_name"], "Unassigned")
                self.assertNotIn("0", snapshot["players"])
                records["state/nfl"]["season"] = "2027"
                with self.assertRaises(ValueError):
                    build_snapshot(client, "123")
                self.assertEqual(build_snapshot(client, "123", week=1)["week"], 1)

    def test_previous_week_context_resolves_departed_players(self):
        client = unittest.mock.Mock()
        client.sources = {}
        client.league.return_value = {"sport": "nfl", "season": "2026", "name": "Test", "status": "in_season", "roster_positions": [], "settings": {}, "scoring_settings": {}}
        client.state.return_value = {"season": "2026", "season_type": "regular", "week": 2}
        client.users.return_value = []
        client.rosters.return_value = []
        client.matchups.side_effect = lambda league, week: [{"roster_id": 1, "players": ["42"], "points": 110}] if week == 1 else []
        client.transactions.side_effect = lambda league, week: [{"drops": {"42": 1}}] if week == 1 else []
        client.traded_picks.return_value = []
        client.drafts.return_value = []
        client.players.return_value = {"42": {"full_name": "Former Player"}}
        snapshot = build_snapshot(client, "123", week=2, include_previous_week=True)
        self.assertEqual(snapshot["previous_week"]["week"], 1)
        self.assertIn("42", snapshot["players"])
        self.assertIn("Former Player", render_briefing(snapshot))
        first_week = build_snapshot(client, "123", week=1, include_previous_week=True)
        self.assertIsNone(first_week["previous_week"])
        self.assertTrue(all(call.args[1] >= 1 for call in client.matchups.call_args_list))


if __name__ == "__main__":
    unittest.main()

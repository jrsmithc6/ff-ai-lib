import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ff_ai_lib.automation import generate, select_week


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.league = {"season": "2026", "status": "in_season"}
        self.state = {"season": "2026", "season_type": "regular", "week": 2}

    def test_current_week_and_explicit_override(self):
        self.assertEqual(select_week(self.league, self.state), 2)
        self.assertEqual(select_week(self.league, self.state, "1"), 1)
        for value in ("0", "19", "1.5", "$(echo bad)"):
            with self.assertRaises(ValueError):
                select_week(self.league, self.state, value)

    def test_offseason_old_league_and_completed_league(self):
        for league, state in (
            (self.league, {**self.state, "season_type": "post"}),
            (self.league, {**self.state, "season": "2027"}),
            ({**self.league, "status": "complete"}, self.state),
        ):
            self.assertIsNone(select_week(league, state, scheduled=True))
            with self.assertRaises(ValueError):
                select_week(league, state)
            self.assertEqual(select_week(league, state, "18"), 18)

    def test_skip_preserves_exports(self):
        client = Mock()
        client.league.return_value = self.league
        client.state.return_value = {**self.state, "season_type": "off"}
        with tempfile.TemporaryDirectory() as directory:
            briefing = Path(directory, "briefing.md")
            briefing.write_text("previous")
            self.assertIsNone(generate(client, directory, scheduled=True))
            self.assertEqual(briefing.read_text(), "previous")
            self.assertFalse(Path(directory, "archive").exists())

    def test_archive_matches_latest_and_failure_preserves_previous(self):
        client = Mock()
        client.league.return_value = self.league
        client.state.return_value = self.state
        snapshot = {"league": self.league, "week": 2, "generated_at": "2026-09-16T13:17:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            with patch("ff_ai_lib.automation.build_snapshot", return_value=snapshot), patch("ff_ai_lib.automation.render_briefing", return_value="brief"):
                generate(client, directory)
            latest = Path(directory, "snapshot.json").read_text()
            archives = list(Path(directory, "archive").rglob("snapshot.json"))
            self.assertEqual(len(archives), 1)
            self.assertEqual(archives[0].read_text(), latest)
            self.assertEqual(json.loads(latest), snapshot)
            with patch("ff_ai_lib.automation.build_snapshot", side_effect=RuntimeError("offline")):
                with self.assertRaises(RuntimeError):
                    generate(client, directory)
            self.assertEqual(Path(directory, "snapshot.json").read_text(), latest)

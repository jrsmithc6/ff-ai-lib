"""Generate exports for scheduled or manually dispatched GitHub Actions runs."""

import json
import os
from pathlib import Path
import re

from .briefing import render_briefing
from .sleeper import DEFAULT_LEAGUE_ID, SleeperClient, build_snapshot, validate_week


def select_week(league, state, requested="", scheduled=False):
    if requested:
        if not re.fullmatch(r"[0-9]{1,2}", requested):
            raise ValueError("Week must be blank or an integer from 1 to 18")
        return validate_week(int(requested))
    current = (
        str(league.get("season")) == str(state.get("season"))
        and state.get("season_type") == "regular"
        and league.get("status") == "in_season"
    )
    if not current:
        if scheduled:
            return None
        raise ValueError("No active matching regular season. Enter an explicit week (1–18).")
    return validate_week(state.get("week"))


def generate(client, output, requested="", scheduled=False):
    league = client.league(DEFAULT_LEAGUE_ID)
    week = select_week(league, client.state(), requested, scheduled)
    if week is None:
        return None
    snapshot = build_snapshot(client, DEFAULT_LEAGUE_ID, week, include_previous_week=True)
    season = str(snapshot["league"]["season"])
    if not re.fullmatch(r"[0-9]{4}", season):
        raise ValueError("Unexpected Sleeper season")
    # Render everything before touching the existing exports. A failed fetch or
    # render cannot replace them, and Actions commits only after this succeeds.
    files = {
        "briefing.md": render_briefing(snapshot),
        "snapshot.json": json.dumps(snapshot, indent=2) + "\n",
    }
    stamp = re.sub(r"[^0-9]", "", snapshot["generated_at"])
    archive = Path(output) / "archive" / season / ("week-%02d" % week) / stamp
    for destination in (Path(output), archive):
        destination.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (destination / name).write_text(content, encoding="utf-8")
    return snapshot


def main():
    snapshot = generate(
        SleeperClient(), Path("exports"),
        requested=os.environ.get("REQUESTED_WEEK", "").strip(),
        scheduled=os.environ.get("GITHUB_EVENT_NAME") == "schedule",
    )
    generated = snapshot is not None
    message = (
        "Generated season %s, week %s. Latest files: exports/briefing.md and exports/snapshot.json."
        % (snapshot["league"]["season"], snapshot["week"])
        if generated else
        "Skipped: this league is not in the current NFL regular season. Existing exports were preserved."
    )
    print(message)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as handle:
            handle.write("generated=%s\n" % str(generated).lower())
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as handle:
            handle.write(message + "\n\nPublication status is shown in the commit step.\n")


if __name__ == "__main__":
    main()

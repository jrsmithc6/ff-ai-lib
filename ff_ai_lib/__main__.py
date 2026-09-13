import argparse
import json
from pathlib import Path

from .briefing import render_briefing
from .sleeper import DEFAULT_LEAGUE_ID, SleeperClient, SleeperError, build_snapshot


def main():
    parser = argparse.ArgumentParser(description="Export a read-only Sleeper briefing for AI chats")
    parser.add_argument("--league", default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--week", type=int, help="NFL regular-season week, 1–18; inferred only for the current regular season")
    parser.add_argument("--output", type=Path, default=Path("exports"))
    parser.add_argument("--cache", type=Path, default=Path(".cache/sleeper"))
    args = parser.parse_args()
    try:
        snapshot = build_snapshot(SleeperClient(args.cache), args.league, args.week)
        briefing = render_briefing(snapshot)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        (args.output / "briefing.md").write_text(briefing, encoding="utf-8")
    except (SleeperError, ValueError, OSError) as exc:
        parser.exit(1, "Export failed: %s\n" % exc)
    print("Briefing: " + str((args.output / "briefing.md").resolve()))
    print("Snapshot: " + str((args.output / "snapshot.json").resolve()))


if __name__ == "__main__":
    main()

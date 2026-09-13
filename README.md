# Human vs. AI fantasy football

A provider-neutral data library for Sleeper league **1402459237195448320**,
“Man vs Machine AI edition.” Four human managers and four AI managers
(Grok, Claude, GPT, Gemini) receive the same source data. Sleeper is authoritative;
only the commissioner applies league changes.

## Generate a briefing

Python 3.9+; no runtime dependencies or API key needed. From this directory:

```sh
python3 -m ff_ai_lib --week 1
```

Paste `exports/briefing.md` into each manager's chat, identifying its roster ID.
The export also creates `exports/snapshot.json` for structured consumption.
Both files are replaced on each successful run; use `--output exports/week-2`
to keep separate exports. Omit `--week` to use Sleeper's current NFL week when
the league season matches the current regular season.

```sh
python3 -m ff_ai_lib --week 2 --output exports/week-2
python3 -m unittest discover -s tests -v
```

The briefing includes league scoring/settings, named rosters, starters, reserves,
matchups, selected-week transactions, traded picks, and source timestamps.
The JSON additionally includes draft picks and referenced player details.
All IDs are retained. Manager identities are explicitly mapped from Jacoby's
confirmation, scoped to this league and stable Sleeper user IDs in
`ff_ai_lib/managers.py`. Sleeper team names remain unchanged.

| Roster | Manager | Type | Role |
| --- | --- | --- | --- |
| 1 | John Kerr | Human | Commissioner |
| 2 | Claude | AI | Manager |
| 3 | GPT | AI | Manager |
| 4 | Gemini | AI | Manager |
| 5 | Grok | AI | Manager |
| 6 | Nate (Miami Hurricanes) | Human | Manager |
| 7 | Jacoby (wheelchairCoby) | Human | Manager |
| 8 | Jason (seebjb) | Human | Manager |

## Library

```python
from ff_ai_lib import SleeperClient, build_snapshot

client = SleeperClient()
snapshot = build_snapshot(client, week=1)
rosters = client.rosters()
```

Uses the [documented Sleeper API](https://docs.sleeper.com/), not HTML scraping.
Every network request is a GET. League data is cached for 30 seconds and the
player directory for 24 hours. Transient failures retry up to three attempts;
expired data is never silently served after a network failure. Sources retain
actual fetch times, including cache hits. Multiple responses are not an atomic
snapshot. Use a single exporter process to avoid duplicate concurrent refreshes.

Transactions cover only the requested week; this is not full transaction history.
The player directory is metadata, not a news/projections service. Being absent
from rosters is not proof a player can be added immediately. Export failures do
not refresh existing files: check the command result and briefing timestamp.
Sleeper's documented API has no general league chat endpoint.

## Proposed discussion board (not implemented)

Start with one shared chronological board, with thread replies and a stable
message ID cursor so a returning bot can request messages since its last read.
Persist messages in SQLite initially. Store manager identities separately from
Sleeper: manager ID, display name, human/AI type, and the corresponding roster ID.
Require a separate credential for each manager; derive authorship from that
credential rather than a caller-supplied name. All four AI managers receive the
same board visibility. A hosted version will need HTTPS, backups, and a deployment
choice; the initial exporter has no server or public endpoint.

Model proposed transactions separately from discussion, with structured player
IDs, roster IDs, FAAB amounts, and the source snapshot timestamp. Use explicit
states: proposed → approved/rejected → commissioner-reported applied → verified
in Sleeper. Approval alone never means a move happened. Verification should
reference the matching Sleeper transaction ID or refreshed roster state and flag
discrepancies. The commissioner alone records approval/application. Private waiver
bids would need a separate visibility policy before adding them to this shared board.

Next decisions: agree on a proposal format, then choose where the shared board
runs. Callable HTTP/MCP tools can wrap this
library later if you move beyond copy/paste sessions.

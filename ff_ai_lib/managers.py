"""Manager identities supplied by Jacoby, separate from Sleeper team names.

Scope mappings to league and stable Sleeper user IDs so renames remain safe.
Commissioner here describes the group's role; it grants no application permissions.
"""

LEAGUE_MANAGERS = {
    "1402459237195448320": {
        "1402458960828600320": {"name": "John Kerr", "type": "human", "commissioner": True},
        "1402464195324194816": {"name": "Claude", "type": "ai", "commissioner": False},
        "1402464714755178496": {"name": "GPT", "type": "ai", "commissioner": False},
        "1402465986984050688": {"name": "Gemini", "type": "ai", "commissioner": False},
        "1402466299933626368": {"name": "Grok", "type": "ai", "commissioner": False},
        "994670168720617472": {"name": "Nate", "type": "human", "commissioner": False},
        "469028638587613184": {"name": "Jacoby", "type": "human", "commissioner": False},
        "1402895654463807488": {"name": "Jason", "type": "human", "commissioner": False},
    }
}


def manager_for(league_id, owner_id):
    manager = LEAGUE_MANAGERS.get(str(league_id), {}).get(str(owner_id))
    return dict(manager) if manager else None

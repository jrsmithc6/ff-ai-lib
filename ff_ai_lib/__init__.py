"""Provider-neutral, read-only fantasy league tools."""

from .sleeper import SleeperClient, SleeperError, build_snapshot

__all__ = ["SleeperClient", "SleeperError", "build_snapshot"]

"""Command registry and ``--manifest`` surface map emitter.

See docs/specs/2026-05-15-mycli-cli-architecture.md § Four design axes #1
(理解 — discover capability without external docs).
"""

from mycli.manifest.registry import CommandSpec, as_manifest_data, register

__all__ = ["CommandSpec", "as_manifest_data", "register"]

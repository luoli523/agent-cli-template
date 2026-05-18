"""Out-of-band notice channel.

``_notice`` carries signals not tied to the current request: a new CLI
version is available, the installed skills are out of sync with the binary,
a service is being deprecated, the user's auth is about to expire.

AI agents should complete the current task first and surface the notice to
the user afterwards. Suppression via env vars (see CLAUDE.md).

See docs/specs/2026-05-15-mycli-cli-architecture.md § ``_notice`` channel.

Concrete payload shapes for each notice type are defined where the writer
lives (T3 runtime / update checker / skill drift detector); this module
just declares the enum of valid keys.
"""

from __future__ import annotations

from enum import Enum


class NoticeType(str, Enum):
    """Valid keys inside the ``_notice`` envelope field."""

    UPDATE = "update"
    SKILLS = "skills"
    DEPRECATION = "deprecation"
    AUTH_EXPIRING = "auth_expiring"

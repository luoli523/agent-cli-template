"""mycli-cli protocol contracts.

These are the message shapes that AI agents parse. Changing any of them is a
contract change requiring explicit approval (see CLAUDE.md § Project Boundaries).

See docs/specs/2026-05-15-mycli-cli-architecture.md § Cross-cutting contracts
for the authoritative definitions.
"""

from mycli.contracts.envelope import Envelope, ErrorEnvelope, Meta
from mycli.contracts.error_type import ErrDetail, ErrorType
from mycli.contracts.exit_code import ExitCode
from mycli.contracts.handle import Handle
from mycli.contracts.notice import NoticeType
from mycli.contracts.risk import RiskClass, RiskDetail

__all__ = [
    "Envelope",
    "ErrDetail",
    "ErrorEnvelope",
    "ErrorType",
    "ExitCode",
    "Handle",
    "Meta",
    "NoticeType",
    "RiskClass",
    "RiskDetail",
]

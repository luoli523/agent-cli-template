"""di-cli protocol contracts.

These are the message shapes that AI agents parse. Changing any of them is a
contract change requiring explicit approval (see CLAUDE.md § Project Boundaries).

See docs/specs/2026-05-15-di-cli-architecture.md § Cross-cutting contracts
for the authoritative definitions.
"""

from di.contracts.envelope import Envelope, ErrorEnvelope, Meta
from di.contracts.error_type import ErrDetail, ErrorType
from di.contracts.exit_code import ExitCode
from di.contracts.handle import Handle
from di.contracts.notice import NoticeType
from di.contracts.risk import RiskClass, RiskDetail

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

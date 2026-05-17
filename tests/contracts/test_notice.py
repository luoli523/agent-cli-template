"""NoticeType: valid keys for the ``_notice`` envelope field."""

from __future__ import annotations

from di.contracts.notice import NoticeType


def test_notice_type_values_match_spec() -> None:
    assert NoticeType.UPDATE.value == "update"
    assert NoticeType.SKILLS.value == "skills"
    assert NoticeType.DEPRECATION.value == "deprecation"
    assert NoticeType.AUTH_EXPIRING.value == "auth_expiring"


def test_notice_type_count_is_exactly_four() -> None:
    assert len(list(NoticeType)) == 4

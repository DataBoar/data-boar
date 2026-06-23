"""Tests for operator-gated issue close contract (#990)."""

from scripts.operator_gated_issue_guard import (
    APPROVED_CLOSE_LABEL,
    close_allowed,
    close_trailer_in_latest_comment,
)


def test_close_trailer_accepts_operator_line() -> None:
    body = (
        "Gate-Close-Approved-By: @FabioLeitao — "
        "completão verde 5 hosts + 26 findings + OK operador"
    )
    assert close_trailer_in_latest_comment(body)


def test_close_trailer_accepts_without_at() -> None:
    assert close_trailer_in_latest_comment("Gate-Close-Approved-By: FabioLeitao\n")


def test_close_trailer_rejects_agent_close_without_trailer() -> None:
    assert not close_trailer_in_latest_comment(
        "Closing after green check-all — looks good!"
    )


def test_close_trailer_rejects_wrong_handle() -> None:
    assert not close_trailer_in_latest_comment("Gate-Close-Approved-By: @other-user")


def test_close_trailer_rejects_pii_gate_marker_only() -> None:
    assert not close_trailer_in_latest_comment("Gate-Change-Approved-By: @FabioLeitao")


def test_close_trailer_rejects_protocol_doc_citing_trailer_in_backticks() -> None:
    """Regression: #406 guard comment must not unlock any close."""
    doc = (
        "Cabresto de fechamento (ADR-0072 / #990):\n"
        "Use no comentário de fechamento: "
        "`Gate-Close-Approved-By: @FabioLeitao` — evidência.\n"
        "O workflow olha só o **último** comentário ou label `gate-close-approved`."
    )
    assert not close_trailer_in_latest_comment(doc)


def test_close_allowed_via_dedicated_label_without_comment() -> None:
    assert close_allowed([APPROVED_CLOSE_LABEL, "operator-gated"], None)


def test_close_allowed_via_latest_comment_not_historical_marker() -> None:
    latest = "Gate-Close-Approved-By: @FabioLeitao — maestro 5 hosts OK"
    assert close_allowed(["operator-gated"], latest)


def test_close_not_allowed_when_latest_lacks_trailer_even_if_label_missing() -> None:
    assert not close_allowed(
        ["operator-gated"],
        "LGTM — closing per green CI",
    )

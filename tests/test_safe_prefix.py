from report.safe_prefix import safe_session_prefix


def test_safe_prefix_uuid_like() -> None:
    s = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    assert safe_session_prefix(s, max_len=16) == "a1b2c3d4-e5f6-78"


def test_safe_prefix_strips_path_chars() -> None:
    p = safe_session_prefix("../../../etc/passwd", max_len=16)
    assert "/" not in p
    assert ".." not in p


def test_safe_prefix_non_uuid() -> None:
    assert safe_session_prefix("cli-exec-report-01", max_len=8) == "cli-exec"

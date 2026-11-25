"""Self-tests for the R7-1 knobs in ``tests.s3_fake.FakeS3``.

These tests verify the fake S3 simulator's hostile knobs behave correctly.
They are in a separate test file so pytest collects them (pytest only collects
files named ``test_*.py``).
"""

from __future__ import annotations

import urllib.parse

import defusedxml.ElementTree as ET

from tests.s3_fake import FakeS3, _reset_list_count


def _next_continuation_token(content: bytes) -> str | None:
    page = ET.fromstring(content)
    for element in page.iter():
        if element.tag.endswith("NextContinuationToken") and element.text:
            return element.text
    return None


def _list_with_token(
    fake: FakeS3, base_query: str, continuation_token: str | None
) -> bytes:
    query = base_query
    if continuation_token:
        query = (
            f"{base_query}&continuation-token="
            f"{urllib.parse.quote(continuation_token, safe='')}"
        )
    resp = fake._list(query, {})
    # #2370 S12: every page before the safety cap must be a real 200 listing.
    assert resp.status_code == 200
    return resp.read()


def _paginated_list(fake: FakeS3, base_query: str, page_count: int) -> list[bytes]:
    """List *page_count* pages, passing each NextContinuationToken like a real client."""
    bodies: list[bytes] = []
    token: str | None = None
    for _ in range(page_count):
        body = _list_with_token(fake, base_query, token)
        bodies.append(body)
        token = _next_continuation_token(body)
    return bodies


def test_self_empty_pages_forever() -> None:
    """Self-test: empty_pages_forever() returns empty pages with IsTruncated=true and new tokens.
    Past the safety cap of 2000 requests the listing answers HTTP 599."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.empty_pages_forever()
    assert fake._fake_empty_pages is True
    assert fake._fake_one_entry is False

    for content in _paginated_list(fake, "?list-type=2", 3):
        page = ET.fromstring(content)
        assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        assert [e.text for e in page.iter() if e.tag.endswith("NextContinuationToken")]
    _reset_list_count(fake)

    token: str | None = None
    for i in range(2000):
        if i > 0:
            content = _list_with_token(fake, "?list-type=2", token)
        else:
            content = _list_with_token(fake, "?list-type=2", None)
        page = ET.fromstring(content)
        truncated = [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        assert truncated, f"request {i} should be truncated"
        token = _next_continuation_token(content)
    # #2370 S12: request 2001 hits the safety cap: HTTP 599 plus a violation.
    resp = fake._list("?list-type=2", {})
    assert resp.status_code == 599
    assert len(fake.violations) == 1


def test_self_one_entry_per_page_forever() -> None:
    """Self-test: one_entry_per_page_forever() returns one entry with IsTruncated=true and
    new tokens. Each entry is a unique key under the requested prefix with real content.
    Past the safety cap of 2000 requests the listing answers HTTP 599."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.one_entry_per_page_forever()
    assert fake._fake_one_entry is True
    assert fake._fake_empty_pages is False
    _reset_list_count(fake)

    base = "?list-type=2&prefix=corpus%2F"
    token: str | None = None
    for n in range(3):
        content = _list_with_token(fake, base, token)
        page = ET.fromstring(content)
        assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        assert [e.text for e in page.iter() if e.tag.endswith("NextContinuationToken")]
        keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
        assert keys == [f"corpus/page-{n + 1:06d}.txt"]
        token = _next_continuation_token(content)

    _reset_list_count(fake)
    token = None
    for i in range(2000):
        content = _list_with_token(fake, base, token)
        page = ET.fromstring(content)
        truncated = [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        assert truncated, f"request {i} should be truncated"
        keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
        assert keys == [f"corpus/page-{i + 1:06d}.txt"]
        token = _next_continuation_token(content)
    # #2370 S12: request 2001 hits the safety cap: HTTP 599 plus a violation.
    resp = fake._list(base, {})
    assert resp.status_code == 599
    assert len(fake.violations) == 1


def test_self_pages_script() -> None:
    """Self-test: pages_script([0, 0, 2, -1]) returns:
    - page 1: 0 entries, truncated
    - page 2: 0 entries, truncated
    - page 3: 2 entries, truncated
    - page 4: 0 entries, NOT truncated (script ended)
    """
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.pages_script([0, 0, 2, -1])

    base = "?list-type=2"
    token: str | None = None
    for expected_keys, expect_truncated in (
        ([], True),
        ([], True),
        (
            [
                "scripted-page-000003-entry-000000.txt",
                "scripted-page-000003-entry-000001.txt",
            ],
            True,
        ),
        ([], False),
    ):
        content = _list_with_token(fake, base, token)
        page = ET.fromstring(content)
        truncated = [e.text for e in page.iter() if e.tag.endswith("IsTruncated")][0]
        assert (truncated == "true") == expect_truncated
        keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
        assert keys == expected_keys
        if expect_truncated:
            token = _next_continuation_token(content)
            if expected_keys:
                sizes = [e.text for e in page.iter() if e.tag.endswith("Size")]
                expected_content = (
                    "synthetic content for scripted page 3 entry 0\n".encode("utf-8")
                )
                expected_size = str(len(expected_content))
                assert sizes == [expected_size, expected_size]


def test_self_pages_script_getobject() -> None:
    """Self-test: with pages_script(), listed keys are fetchable via GetObject
    with body length matching the declared Size."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.pages_script([1, 2, -1])

    base = "?list-type=2&prefix=corpus%2F"
    content1 = _list_with_token(fake, base, None)
    page1 = ET.fromstring(content1)
    keys1 = [e.text for e in page1.iter() if e.tag.endswith("Key")]
    sizes1 = [e.text for e in page1.iter() if e.tag.endswith("Size")]
    assert keys1 == ["corpus/scripted-page-000001-entry-000000.txt"]
    expected_content1 = "synthetic content for scripted page 1 entry 0\n".encode(
        "utf-8"
    )
    assert sizes1 == [str(len(expected_content1))]
    tok1 = _next_continuation_token(content1)

    content2 = _list_with_token(fake, base, tok1)
    page2 = ET.fromstring(content2)
    keys2 = [e.text for e in page2.iter() if e.tag.endswith("Key")]
    sizes2 = [e.text for e in page2.iter() if e.tag.endswith("Size")]
    assert keys2 == [
        "corpus/scripted-page-000002-entry-000000.txt",
        "corpus/scripted-page-000002-entry-000001.txt",
    ]
    expected_content2 = "synthetic content for scripted page 2 entry 0\n".encode(
        "utf-8"
    )
    assert sizes2 == [str(len(expected_content2)), str(len(expected_content2))]

    assert keys1 != keys2
    assert keys2[0] != keys2[1]

    get_resp1 = fake._get(keys1[0], {})
    assert get_resp1.status_code == 200
    body1 = b"".join(get_resp1.stream)
    assert len(body1) == int(sizes1[0])

    for key, expected_size in zip(keys2, sizes2):
        get_resp = fake._get(key, {})
        assert get_resp.status_code == 200
        body = b"".join(get_resp.stream)
        assert len(body) == int(expected_size)


def test_self_one_entry_per_page_forever_getobject() -> None:
    """Self-test: with one_entry_per_page_forever(), listing two pages gives two different
    keys under the prefix, and GetObject on each returns 200 with body length equal
    to the declared size."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.one_entry_per_page_forever()

    base = "?list-type=2&prefix=corpus%2F"
    content1 = _list_with_token(fake, base, None)
    page1 = ET.fromstring(content1)
    keys1 = [e.text for e in page1.iter() if e.tag.endswith("Key")]
    assert keys1 == ["corpus/page-000001.txt"]
    tok = _next_continuation_token(content1)

    content2 = _list_with_token(fake, base, tok)
    page2 = ET.fromstring(content2)
    keys2 = [e.text for e in page2.iter() if e.tag.endswith("Key")]
    assert keys2 == ["corpus/page-000002.txt"]

    assert keys1 != keys2

    get_resp1 = fake._get(keys1[0], {})
    assert get_resp1.status_code == 200
    body1 = b"".join(get_resp1.stream)
    assert len(body1) == len("synthetic content for page 1\n".encode("utf-8"))

    get_resp2 = fake._get(keys2[0], {})
    assert get_resp2.status_code == 200
    body2 = b"".join(get_resp2.stream)
    assert len(body2) == len("synthetic content for page 2\n".encode("utf-8"))


def test_self_pages_script_safety_cap_returns_599() -> None:
    """Self-test: pages_script() returns 599 and records violation when safety cap exceeded."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.pages_script([1, -1])

    content = _list_with_token(fake, "?list-type=2", None)
    page = ET.fromstring(content)
    assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == ["true"]
    token = _next_continuation_token(content)

    _list_with_token(fake, "?list-type=2", token)

    resp = fake._list("?list-type=2", {})
    assert resp.status_code == 599
    assert fake.violations == [
        "pages_script safety cap exceeded: request 3 past end of script (length 2)"
    ]


def test_self_empty_pages_forever_safety_cap_returns_599() -> None:
    """Self-test: empty_pages_forever() returns 599 and records violation past 2000 requests."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.empty_pages_forever()
    _reset_list_count(fake)

    token: str | None = None
    for _ in range(2000):
        content = _list_with_token(fake, "?list-type=2", token)
        assert ET.fromstring(content) is not None
        token = _next_continuation_token(content)

    resp = fake._list("?list-type=2", {})
    assert resp.status_code == 599
    assert len(fake.violations) == 1
    assert "empty_pages_forever safety cap exceeded" in fake.violations[0]


def test_self_one_entry_per_page_forever_safety_cap_returns_599() -> None:
    """Self-test: one_entry_per_page_forever() returns 599 and records violation past 2000 requests."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.one_entry_per_page_forever()
    _reset_list_count(fake)

    base = "?list-type=2&prefix=corpus%2F"
    token: str | None = None
    for _ in range(2000):
        content = _list_with_token(fake, base, token)
        assert ET.fromstring(content) is not None
        token = _next_continuation_token(content)

    resp = fake._list(base, {})
    assert resp.status_code == 599
    assert len(fake.violations) == 1
    assert "one_entry_per_page_forever safety cap exceeded" in fake.violations[0]

"""Self-tests for the R7-1 knobs in ``tests.s3_fake.FakeS3``.

These tests verify the fake S3 simulator's hostile knobs behave correctly.
They are in a separate test file so pytest collects them (pytest only collects
files named ``test_*.py``).
"""

from tests.s3_fake import FakeS3, _reset_list_count
import defusedxml.ElementTree as ET


def test_self_empty_pages_forever() -> None:
    """Self-test: empty_pages_forever() returns empty pages with IsTruncated=true and new tokens.
    Ends after safety cap of 2000 requests (IsTruncated=false)."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.empty_pages_forever()
    assert fake._fake_empty_pages is True
    assert fake._fake_one_entry is False

    # First 3 requests: empty, truncated, new token.
    for _ in range(3):
        resp = fake._list("?list-type=2", {})
        page = ET.fromstring(resp.read())
        assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        assert [e.text for e in page.iter() if e.tag.endswith("NextContinuationToken")]
    _reset_list_count(fake)

    # Safety cap test: request 2001 times, 2000th is truncated, 2001st is not.
    for i in range(2001):
        resp = fake._list("?list-type=2", {})
        content = resp.read()
        page = ET.fromstring(content)
        truncated = [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        if i < 2000:
            assert truncated, f"request {i} should be truncated"
        else:
            assert not truncated, f"request {i} should not be truncated (safety cap)"


def test_self_one_entry_per_page_forever() -> None:
    """Self-test: one_entry_per_page_forever() returns one entry with IsTruncated=true and
    new tokens. Each entry is a unique key under the requested prefix with real content.
    Ends after safety cap of 2000 requests (IsTruncated=false)."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.one_entry_per_page_forever()
    assert fake._fake_one_entry is True
    assert fake._fake_empty_pages is False
    _reset_list_count(fake)

    # First 3 requests: one entry per page, each with unique key under prefix.
    for n in range(3):
        resp = fake._list("?list-type=2&prefix=corpus%2F", {})
        content = resp.read()
        page = ET.fromstring(content)
        assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        assert [e.text for e in page.iter() if e.tag.endswith("NextContinuationToken")]
        # Exactly one contents entry with unique key under prefix.
        keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
        assert keys == [f"corpus/page-{n + 1:06d}.txt"]

    # Safety cap test: request 2001 times, 2000th is truncated, 2001st is not.
    _reset_list_count(fake)
    for i in range(2001):
        resp = fake._list("?list-type=2&prefix=corpus%2F", {})
        content = resp.read()
        page = ET.fromstring(content)
        truncated = [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == [
            "true"
        ]
        if i < 2000:
            assert truncated, f"request {i} should be truncated"
            keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
            assert keys == [f"corpus/page-{i + 1:06d}.txt"]
        else:
            assert not truncated, f"request {i} should not be truncated (safety cap)"
            keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
            assert keys == []


def test_self_pages_script() -> None:
    """Self-test: pages_script([0, 0, 2, -1]) returns:
    - page 1: 0 entries, truncated
    - page 2: 0 entries, truncated
    - page 3: 2 entries, truncated
    - page 4: 0 entries, NOT truncated (script ended)
    """
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.pages_script([0, 0, 2, -1])

    # Page 1: 0 entries
    resp = fake._list("?list-type=2", {})
    page = ET.fromstring(resp.read())
    assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == ["true"]
    assert [e.text for e in page.iter() if e.tag.endswith("Key")] == []

    # Page 2: 0 entries
    resp = fake._list("?list-type=2", {})
    page = ET.fromstring(resp.read())
    assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == ["true"]
    assert [e.text for e in page.iter() if e.tag.endswith("Key")] == []

    # Page 3: 2 entries (unique keys under prefix, with real content)
    resp = fake._list("?list-type=2", {})
    page = ET.fromstring(resp.read())
    assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == ["true"]
    keys = [e.text for e in page.iter() if e.tag.endswith("Key")]
    # Keys should be unique and under the (empty) prefix
    assert keys == [
        "scripted-page-000003-entry-000000.txt",
        "scripted-page-000003-entry-000001.txt",
    ]
    # Size elements should match content length
    sizes = [e.text for e in page.iter() if e.tag.endswith("Size")]
    # Compute expected size from the content pattern used in the fake
    expected_content = "synthetic content for scripted page 3 entry 0\n".encode("utf-8")
    expected_size = str(len(expected_content))
    assert sizes == [expected_size, expected_size]

    # Page 4: 0 entries, NOT truncated (script ended with -1)
    resp = fake._list("?list-type=2", {})
    page = ET.fromstring(resp.read())
    assert [e.text for e in page.iter() if e.tag.endswith("IsTruncated")] == ["false"]
    assert [e.text for e in page.iter() if e.tag.endswith("Key")] == []


def test_self_pages_script_getobject() -> None:
    """Self-test: with pages_script(), listed keys are fetchable via GetObject
    with body length matching the declared Size."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.pages_script([1, 2, -1])

    # Page 1: 1 entry with prefix "corpus/"
    resp = fake._list("?list-type=2&prefix=corpus%2F", {})
    page1 = ET.fromstring(resp.read())
    keys1 = [e.text for e in page1.iter() if e.tag.endswith("Key")]
    sizes1 = [e.text for e in page1.iter() if e.tag.endswith("Size")]
    assert keys1 == ["corpus/scripted-page-000001-entry-000000.txt"]
    expected_content1 = "synthetic content for scripted page 1 entry 0\n".encode(
        "utf-8"
    )
    assert sizes1 == [str(len(expected_content1))]

    # Page 2: 2 entries with same prefix
    resp = fake._list("?list-type=2&prefix=corpus%2F", {})
    page2 = ET.fromstring(resp.read())
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

    # Keys must be different across pages
    assert keys1 != keys2
    assert keys2[0] != keys2[1]

    # GetObject on first key should return 200 with matching body length.
    get_resp1 = fake._get(keys1[0], {})
    assert get_resp1.status_code == 200
    body1 = b"".join(get_resp1.stream)
    assert len(body1) == int(sizes1[0])

    # GetObject on second page keys should return 200 with matching body length.
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

    # Page 1: list with prefix corpus/
    resp = fake._list("?list-type=2&prefix=corpus%2F", {})
    page1 = ET.fromstring(resp.read())
    keys1 = [e.text for e in page1.iter() if e.tag.endswith("Key")]
    assert keys1 == ["corpus/page-000001.txt"]

    # Page 2: list with same prefix
    resp = fake._list("?list-type=2&prefix=corpus%2F", {})
    page2 = ET.fromstring(resp.read())
    keys2 = [e.text for e in page2.iter() if e.tag.endswith("Key")]
    assert keys2 == ["corpus/page-000002.txt"]

    # Keys must be different.
    assert keys1 != keys2

    # GetObject on first key should return 200 with matching body length.
    get_resp1 = fake._get(keys1[0], {})
    assert get_resp1.status_code == 200
    body1 = b"".join(get_resp1.stream)
    assert len(body1) == len("synthetic content for page 1\n".encode("utf-8"))

    # GetObject on second key should return 200 with matching body length.
    get_resp2 = fake._get(keys2[0], {})
    assert get_resp2.status_code == 200
    body2 = b"".join(get_resp2.stream)
    assert len(body2) == len("synthetic content for page 2\n".encode("utf-8"))


def test_self_pages_script_safety_cap_returns_599() -> None:
    """Self-test: pages_script() returns 599 and records violation when safety cap exceeded."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.pages_script([1, -1])  # Script of length 2

    # First 2 requests: normal responses
    resp = fake._list("?list-type=2", {})
    assert resp.status_code == 200
    resp = fake._list("?list-type=2", {})
    assert resp.status_code == 200

    # 3rd request: past end of script, should return 599
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

    # Request 2000: still 200
    for _ in range(2000):
        resp = fake._list("?list-type=2", {})
        assert resp.status_code == 200

    # Request 2001: should return 599
    resp = fake._list("?list-type=2", {})
    assert resp.status_code == 599
    assert len(fake.violations) == 1
    assert "empty_pages_forever safety cap exceeded" in fake.violations[0]


def test_self_one_entry_per_page_forever_safety_cap_returns_599() -> None:
    """Self-test: one_entry_per_page_forever() returns 599 and records violation past 2000 requests."""
    fake = FakeS3("test-bucket", {}, "host.example", "virtual", "us-east-1")
    fake.one_entry_per_page_forever()
    _reset_list_count(fake)

    # Request 2000: still 200
    for _ in range(2000):
        resp = fake._list("?list-type=2&prefix=corpus%2F", {})
        assert resp.status_code == 200

    # Request 2001: should return 599
    resp = fake._list("?list-type=2&prefix=corpus%2F", {})
    assert resp.status_code == 599
    assert len(fake.violations) == 1
    assert "one_entry_per_page_forever safety cap exceeded" in fake.violations[0]

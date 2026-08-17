from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.native_host import HostError, store_record, validate_record  # noqa: E402
from viewer.server import ArchiveReader, is_loopback_host  # noqa: E402


def candidate(url: str = "http://127.0.0.1:8787/") -> dict[str, object]:
    return {
        "version": 1,
        "url": url,
        "title": "Synthetic note",
        "text": "Local demo content only.",
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def test_store_is_content_addressed_and_viewer_is_read_only(tmp_path: Path) -> None:
    database = tmp_path / "archive.sqlite3"
    record = validate_record(candidate())
    first = store_record(record, database)
    second = store_record(record, database)
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert first["record_id"] == second["record_id"]

    reader = ArchiveReader(database)
    rows = reader.list_records()
    assert len(rows) == 1
    assert reader.get_record(rows[0]["record_id"])["body_text"] == "Local demo content only."


@pytest.mark.parametrize("url", ["https://example.com/", "http://127.0.0.1:8788/", "http://user@127.0.0.1:8787/"])
def test_remote_or_credentialed_urls_are_rejected(url: str) -> None:
    with pytest.raises(HostError):
        validate_record(candidate(url))


def test_viewer_host_header_is_loopback_only() -> None:
    assert is_loopback_host("127.0.0.1:8765")
    assert is_loopback_host("localhost:8765")
    assert not is_loopback_host("example.com")
    assert not is_loopback_host("127.0.0.1.example.com:8765")

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import sys
from typing import BinaryIO
from urllib.parse import urlsplit


ALLOWED_ORIGIN = ("http", "127.0.0.1", 8787)
MAX_MESSAGE_BYTES = 1_000_000
MAX_TEXT_CHARS = 100_000
DATA_ROOT = Path.home() / ".authorized-web-archiver"
DATABASE_PATH = DATA_ROOT / "archive.sqlite3"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
EXPECTED_KEYS = {"version", "url", "title", "text", "captured_at"}


class HostError(ValueError):
    pass


def validate_record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        raise HostError("record shape is invalid")
    if value["version"] != 1:
        raise HostError("unsupported record version")

    url = value["url"]
    title = value["title"]
    text = value["text"]
    captured_at = value["captured_at"]
    if not isinstance(url, str) or not _allowed_url(url):
        raise HostError("URL is outside the exact localhost allowlist")
    if not isinstance(title, str) or not 1 <= len(title) <= 200 or _has_control(title):
        raise HostError("title is invalid")
    if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT_CHARS or "\x00" in text:
        raise HostError("page text is invalid")
    if not isinstance(captured_at, str):
        raise HostError("captured_at is invalid")
    try:
        parsed_time = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise HostError("captured_at is invalid") from error
    if parsed_time.tzinfo is None:
        raise HostError("captured_at must include a timezone")
    return {
        "version": 1,
        "url": url,
        "title": title.strip(),
        "text": text.replace("\r\n", "\n").replace("\r", "\n").strip(),
        "captured_at": parsed_time.astimezone(timezone.utc).isoformat(),
    }


def store_record(record: dict[str, object], database_path: Path = DATABASE_PATH) -> dict[str, object]:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO records
                (url, title, body_text, captured_at, record_sha256, stored_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record["url"],
                record["title"],
                record["text"],
                record["captured_at"],
                digest,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        if cursor.rowcount:
            record_id = cursor.lastrowid
            duplicate = False
        else:
            row = connection.execute("SELECT record_id FROM records WHERE record_sha256 = ?", (digest,)).fetchone()
            record_id = int(row[0])
            duplicate = True
        connection.commit()
        return {"ok": True, "record_id": record_id, "sha256": digest, "duplicate": duplicate}
    finally:
        connection.close()


def read_message(stream: BinaryIO) -> object | None:
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise HostError("truncated message header")
    length = struct.unpack("<I", header)[0]
    if not 1 <= length <= MAX_MESSAGE_BYTES:
        raise HostError("message length is invalid")
    payload = stream.read(length)
    if len(payload) != length:
        raise HostError("truncated message payload")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostError("message is not valid UTF-8 JSON") from error


def write_message(stream: BinaryIO, value: object) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(struct.pack("<I", len(payload)))
    stream.write(payload)
    stream.flush()


def main() -> int:
    while True:
        try:
            candidate = read_message(sys.stdin.buffer)
            if candidate is None:
                return 0
            response = store_record(validate_record(candidate))
        except HostError as error:
            response = {"ok": False, "error": str(error)}
        except (OSError, sqlite3.Error):
            response = {"ok": False, "error": "local storage is unavailable"}
        write_message(sys.stdout.buffer, response)


def _allowed_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        (parsed.scheme, parsed.hostname, port) == ALLOWED_ORIGIN
        and parsed.username is None
        and parsed.password is None
    )


def _has_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


if __name__ == "__main__":
    raise SystemExit(main())

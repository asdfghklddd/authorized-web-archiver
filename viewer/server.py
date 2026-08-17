from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
from typing import Any
from urllib.parse import urlsplit


DATA_ROOT = Path.home() / ".authorized-web-archiver"
DATABASE_PATH = DATA_ROOT / "archive.sqlite3"
WEB_ROOT = Path(__file__).with_name("web")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class ArchiveReader:
    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path.resolve()

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.is_file():
            raise FileNotFoundError("archive database does not exist")
        connection = sqlite3.connect(f"file:{self.database_path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def list_records(self) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT record_id, url, title, captured_at, record_sha256,
                       substr(body_text, 1, 180) AS excerpt
                  FROM records
                 ORDER BY captured_at DESC, record_id DESC
                 LIMIT 100
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def get_record(self, record_id: int) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT record_id, url, title, body_text, captured_at, record_sha256, stored_at
                  FROM records
                 WHERE record_id = ?
                """,
                (record_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()


def is_loopback_host(value: str) -> bool:
    host = value.strip().lower().rsplit(":", 1)[0].strip("[]")
    return host in {"127.0.0.1", "localhost"}


class ViewerHandler(BaseHTTPRequestHandler):
    archive = ArchiveReader()
    protocol_version = "HTTP/1.1"
    server_version = "AuthorizedWebArchive/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if not is_loopback_host(self.headers.get("Host", "")):
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "loopback host required"})
            return
        path = urlsplit(self.path).path
        try:
            if path in STATIC_FILES:
                name, content_type = STATIC_FILES[path]
                self._send_static(name, content_type)
                return
            if path == "/api/records":
                self._send_json(HTTPStatus.OK, {"records": self.archive.list_records()})
                return
            match = re.fullmatch(r"/api/records/(\d{1,10})", path)
            if match:
                record = self.archive.get_record(int(match.group(1)))
                self._send_json(HTTPStatus.OK, record) if record else self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            if path == "/healthz":
                self._send_json(HTTPStatus.OK, {"ok": True, "readonly": True})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except (FileNotFoundError, sqlite3.Error):
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "archive is unavailable"})

    def _headers(self, content_type: str, length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; "
            "object-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'",
        )

    def _send_json(self, status: HTTPStatus, value: object) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status.value)
        self._headers("application/json; charset=utf-8", len(payload))
        self.end_headers()
        self.wfile.write(payload)

    def _send_static(self, name: str, content_type: str) -> None:
        payload = (WEB_ROOT / name).read_bytes()
        self.send_response(HTTPStatus.OK.value)
        self._headers(content_type, len(payload))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


def make_handler(archive: ArchiveReader) -> type[ViewerHandler]:
    class BoundHandler(ViewerHandler):
        pass

    BoundHandler.archive = archive
    return BoundHandler


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only local archive viewer")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(ArchiveReader()))
    print(f"Read-only viewer: http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

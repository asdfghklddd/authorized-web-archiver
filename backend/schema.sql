CREATE TABLE IF NOT EXISTS records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    body_text TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    record_sha256 TEXT NOT NULL UNIQUE,
    stored_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS records_captured_at_idx
    ON records(captured_at DESC);

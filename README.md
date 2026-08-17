# Authorized Web Archiver

A consent-driven, localhost-only reference implementation for archiving a web page into content-addressed SQLite and reviewing it through a read-only local viewer.

> Portfolio edition: this is a fresh, generic implementation. It contains no platform-specific endpoints, account flows, proprietary content, personal research records, credentials, or history from the private production repository.

## Trust boundary

```text
user toolbar click
      ↓ activeTab (temporary)
exact localhost allowlist
      ↓ validated native message
parameterized SQLite + SHA-256
      ↓ read-only connection
127.0.0.1 viewer + strict CSP
```

The public demo deliberately archives only `http://127.0.0.1:8787`. Supporting another site requires an explicit code change and a new review; there is no arbitrary-URL input.

## What it demonstrates

- Chrome Manifest V3 with a user-gesture capture flow
- least-privilege `activeTab`, `scripting`, and `nativeMessaging` permissions
- duplicated policy enforcement across the extension and native trust boundary
- bounded native messaging, strict record schemas, parameterized SQL, deduplication, and SHA-256 integrity
- a loopback-only viewer with fixed routes, read-only SQLite, safe DOM APIs, and restrictive headers
- synthetic fixtures plus JavaScript and Python tests

## Explore locally

Run the synthetic source page:

```powershell
python demo\server.py
```

Load this repository as an unpacked Chrome extension, copy its generated extension ID, then register the local Native Messaging host:

```powershell
powershell -ExecutionPolicy Bypass -File backend\install_native_host.ps1 -ExtensionId <32-character-extension-id>
```

The installer validates the ID and derives the launcher path from the repository; no personal path or extension ID is committed. Click the extension on the synthetic page to create a record.

Start the local viewer after the first capture:

```powershell
python viewer\server.py
```

Open `http://127.0.0.1:8765`.

## Verify

```powershell
npm ci
npm test
python -m pip install -r requirements-dev.txt
python -m pytest
```

See [SECURITY.md](SECURITY.md) for the enforced boundary and responsible-use constraint.

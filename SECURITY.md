# Security model

This repository is intentionally narrower than a general-purpose crawler.

- Capture requires a toolbar click and Chrome's temporary `activeTab` grant.
- Both extension and native host enforce the exact origin `http://127.0.0.1:8787`.
- The extension reads visible text, title, and URL only. It does not read authentication state, forms, browser storage, or hidden network traffic.
- Native messages are length-bounded and schema-validated; SQLite writes are parameterized and content-addressed with SHA-256.
- The viewer binds to `127.0.0.1`, validates the Host header, uses a fixed read-only database, exposes fixed routes, and sends a restrictive CSP.
- No arbitrary URL, filesystem path, SQL, or shell execution interface is provided.

Use the design only for content you own or are explicitly authorized to archive.

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PAGE = b"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Synthetic Research Note</title><main><h1>Synthetic Research Note</h1><p>This page is local, fictional, and created only to exercise the consent-driven archive flow.</p><h2>Finding</h2><p>A narrow allowlist makes the data boundary visible and testable.</p></main></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        host = (self.headers.get("Host") or "").lower()
        if host != "127.0.0.1:8787" or self.path not in {"/", "/index.html"}:
            self.send_error(HTTPStatus.NOT_FOUND.value)
            return
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(PAGE)))
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'none'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(PAGE)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8787), Handler)
    print("Synthetic source: http://127.0.0.1:8787/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

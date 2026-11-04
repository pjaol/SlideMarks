"""SPIKE: HTTPS static server for the task pane, plus POST /log and /file endpoints so
the add-in can report probe results and upload the saved document for inspection."""

import base64
import http.server
import json
import ssl
import time
from pathlib import Path

HERE = Path(__file__).parent
CERTS = Path.home() / ".office-addin-dev-certs"
RESULTS = HERE / "results"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/cmd":
            cmd_file = RESULTS / "cmd.txt"
            cmd = cmd_file.read_text().strip() if cmd_file.exists() else ""
            if cmd:
                cmd_file.unlink()
            body = cmd.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        RESULTS.mkdir(exist_ok=True)
        stamp = time.strftime("%H%M%S")
        if self.path == "/log":
            entry = json.loads(body)
            with open(RESULTS / "log.jsonl", "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        elif self.path.startswith("/file"):
            payload = json.loads(body)
            (RESULTS / f"{stamp}-{payload['name']}").write_bytes(base64.b64decode(payload["data"]))
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("localhost", 3443), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERTS / "localhost.crt", CERTS / "localhost.key")
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print("serving https://localhost:3443", flush=True)
    server.serve_forever()

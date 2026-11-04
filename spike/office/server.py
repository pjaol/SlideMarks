"""SPIKE: HTTPS static server for the task pane, plus POST /log and /file endpoints so
the add-in can report probe results and upload the saved document for inspection."""

import base64
import http.server
import io
import sys
import json
import ssl
import time
from pathlib import Path

HERE = Path(__file__).parent
CERTS = Path.home() / ".office-addin-dev-certs"
RESULTS = HERE / "results"
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
TTF = ROOT / "dist/fonts/SlideMarks-Regular.ttf"


def prepare(kind: str, data: bytes, mode: str) -> bytes:
    """Return a copy with the embed-fonts flag set and (mode=full) SlideMarks embedded."""
    if kind == "pptx":
        from pptx import Presentation
        from slidemarks_build.specimen_pptx import _embed_font
        doc = Presentation(io.BytesIO(data))
        if mode == "full":
            _embed_font(doc, TTF)
        else:
            doc.part._element.set("embedTrueTypeFonts", "1")
    else:
        from docx import Document
        from docx.oxml.ns import qn
        from slidemarks_build.specimen_docx import _embed_font
        doc = Document(io.BytesIO(data))
        if mode == "full":
            _embed_font(doc, TTF)
        else:
            settings = doc.settings.element
            if settings.find(qn("w:embedTrueTypeFonts")) is None:
                zoom = settings.find(qn("w:zoom"))
                el = settings.makeelement(qn("w:embedTrueTypeFonts"), {})
                (zoom.addnext(el) if zoom is not None else settings.insert(0, el))
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/cmd"):
            host = self.path.partition("host=")[2]
            cmd_file = RESULTS / (f"cmd-{host}.txt" if host else "cmd.txt")
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
        elif self.path.startswith("/prepare"):
            payload = json.loads(body)
            result = prepare(payload["kind"], base64.b64decode(payload["data"]), payload.get("mode", "full"))
            (RESULTS / f"{stamp}-prepared-{payload.get('mode','full')}.{payload['kind']}").write_bytes(result)
            out = json.dumps({"data": base64.b64encode(result).decode()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
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

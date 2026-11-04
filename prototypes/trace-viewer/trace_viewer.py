"""Serve a small read-only viewer for local Weight Lab trace telemetry."""

import argparse
import json
import re
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


HERE = Path(__file__).resolve().parent
SAFE_LABEL = re.compile(r"[a-zA-Z0-9_.-]{1,140}\Z")
NUMBERS = (
    "step", "processed_tokens", "prompt_tokens", "total_prompt_tokens",
    "completion_tokens", "decode_elapsed_ms", "decode_ms", "prefill_ms",
    "elapsed_ms", "load_elapsed_ms", "token_id", "mismatches", "states",
    "native_next_matches",
)
LOG_NAMES = {"native.log", "native-stderr.log", "native.stderr.log"}


def trace_logs(workspace):
    root = workspace / "runs"
    paths = (
        path for pattern in ("*/*.log", "*/*/*.log")
        for path in root.glob(pattern)
        if path.name in LOG_NAMES and path.is_file()
        and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
    )
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)[:24]


def events_from(path):
    with path.open("rb") as stream:
        beginning = stream.read(2)
        start = max(0, path.stat().st_size - 2**20)
        encoding = "utf-16-le" if beginning == b"\xff\xfe" else "utf-8"
        stream.seek(start - (start % 2) if encoding == "utf-16-le" else start)
        lines = stream.read(2**20).decode(encoding, "replace").splitlines()
    events = []
    for line in lines:
        marker = re.search(r"\bWR_(?:LIVE|HEAD) (\{.*\})", line)
        if marker is None:
            continue
        try:
            value = json.loads(marker.group(1))
        except ValueError:
            continue
        if not isinstance(value, dict):
            continue
        name = value.get("event", "")
        if not isinstance(name, str) or not SAFE_LABEL.fullmatch(name):
            continue
        event = {"event": name}
        for key in NUMBERS:
            item = value.get(key)
            if type(item) in (int, float) and -1e20 <= item <= 1e20:
                event[key] = item
        for key in ("case_id", "id", "finish_reason", "device"):
            item = value.get(key)
            if isinstance(item, str) and SAFE_LABEL.fullmatch(item):
                event[key] = item
        stamp = value.get("timestamp_utc")
        if isinstance(stamp, str) and len(stamp) <= 32:
            try:
                event["time"] = datetime.fromisoformat(stamp.replace("Z", "+00:00")).isoformat()
            except ValueError:
                pass
        if type(value.get("eog")) is bool:
            event["eog"] = value["eog"]
        events.append(event)
    return events[-2400:]


def snapshot(workspace, selection):
    logs = trace_logs(workspace)
    root = workspace / "runs"
    choices = {str(path.relative_to(root)).replace("\\", "/"): path for path in logs}
    active = choices.get(selection)
    events = events_from(active) if active else []
    if active is None:
        for path in choices.values():
            events = events_from(path)
            if events:
                active = path
                break
    capture = any(item["event"].startswith("sequence_") for item in events)
    case = next((item.get("case_id") or item.get("id") for item in reversed(events)
                 if item.get("case_id") or item.get("id")), None)
    tokens = [item for item in events if item["event"] == "token" and item.get("case_id") == case
              and "decode_elapsed_ms" in item and "step" in item]
    captures = [item for item in events if item["event"] == "sequence_capture_progress"
                and "elapsed_ms" in item and "processed_tokens" in item]
    latest = tokens[-1] if tokens else {}
    latest_capture = captures[-1] if captures else {}
    pace = tokens[::max(1, len(tokens) // 100)]
    if pace and pace[-1] != latest:
        pace.append(latest)
    newest = events[-1] if events else {}
    stage_events = [item for item in events
                    if item["event"] != "token" or item is latest]
    finish = next((item.get("finish_reason") for item in reversed(events)
                   if item["event"] == "prompt_complete" and item.get("case_id") == case), None)
    status = "Waiting for trace"
    if newest.get("event") == "run_complete":
        status = "Token cap reached" if finish == "length" else "Trace complete"
    elif newest.get("event") == "sequence_run_complete":
        status = "Capture complete"
    elif events:
        status = "Watching" if time.time() - active.stat().st_mtime < 10 else "Last recorded"
    weights = None
    heatmap = HERE / "weight-change.json"
    if heatmap.is_file():
        weights = json.loads(heatmap.read_bytes())
    return {
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "run": str(active.relative_to(root)).replace("\\", "/") if active else None,
        "choices": list(choices),
        "status": status,
        "case": case,
        "capture": capture,
        "latest_capture": latest_capture,
        "finish": finish,
        "latest": newest,
        "latest_token": latest,
        "pace": (
            [[item["elapsed_ms"] / 1000, item["processed_tokens"]] for item in captures]
            if capture else [[item["decode_elapsed_ms"] / 1000, item["step"] + 1] for item in pace]
        ),
        "events": stage_events[-22:],
        "weights": weights,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         "style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; object-src 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.send(403, "text/plain", b"Local origin required")
            return
        url = urlsplit(self.path)
        if url.path == "/":
            self.send(200, "text/html; charset=utf-8", (HERE / "index.html").read_bytes())
        elif url.path == "/api/live":
            try:
                selection = parse_qs(url.query).get("run", [None])[0]
                data = snapshot(self.server.workspace, selection)
                self.send(200, "application/json", json.dumps(data, allow_nan=False).encode())
            except (OSError, ValueError):
                self.send(503, "application/json", b'{"status":"Waiting for the next complete trace read"}')
        else:
            self.send(404, "text/plain", b"Not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=HERE.parent)
    parser.add_argument("--port", type=int, default=8769)
    options = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", options.port), Handler)
    server.workspace = options.workspace.resolve(strict=True)
    print(f"Trace viewer at http://127.0.0.1:{server.server_port}", flush=True)
    with server:
        server.serve_forever()

"""Serve a small read-only viewer for local Weight Lab trace telemetry."""

import argparse
from collections import deque
import json
import os
import re
import time
from datetime import datetime, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit


HERE = Path(__file__).resolve().parent
SAFE_LABEL = re.compile(r"[a-zA-Z0-9_.-]{1,140}\Z")
COMPARISON_NAME = re.compile(r"weight-change(?:-[a-zA-Z0-9_.-]{1,96})?\.json\Z")
ORDINARY_GROUP = re.compile(r"(?:(?:agieval|ugmath)-batch-[0-9]{2}|critical-pair)\Z")
EVENT_MARKER = re.compile(r"\bWR_(?:LIVE|HEAD) (\{.*\})")
NUMBERS = (
    "step", "processed_tokens", "prompt_tokens", "total_prompt_tokens",
    "completion_tokens", "decode_elapsed_ms", "decode_ms", "prefill_ms",
    "elapsed_ms", "load_elapsed_ms", "token_id", "mismatches", "states",
    "native_next_matches", "captured_rows", "margin",
)
LOG_NAMES = {"native.log", "native-stderr.log", "native.stderr.log"}
PHYSICAL_LOG_NAMES = {"train-primary.stderr.log", "train-additional.stderr.log", "known-euler.stderr.log"}
MAX_SCAN_ENTRIES = 8192
MAX_RUNS = 24
LEGACY_RUN_SLOTS = 6
MAX_LOG_BYTES = 2**20
MAX_LOG_EVENTS = 2400
MAX_PACE_POINTS = 640
MAX_COMPARISONS = 32
MAX_COMPARISON_BYTES = 2**21
MAX_COMPARISON_CELLS = 65536
CURRENT_WEIGHT = "weight-change.json"
REFERENCE_WEIGHT = "weight-change-reference.json"
ASSETS = {"/": ("index.html", "text/html"), "/viewer.css": ("viewer.css", "text/css"),
          "/viewer.js": ("viewer.js", "text/javascript"), "/favicon.svg": ("favicon.svg", "image/svg+xml")}


def trace_logs(workspace):
    return discover_logs(workspace, int(time.monotonic() // 2))


@lru_cache(maxsize=4)
def discover_logs(workspace, tick):
    root = (workspace / "runs").resolve()
    pending = deque([(root, ())])
    entries, paths = 0, []
    while pending and entries < MAX_SCAN_ENTRIES:
        directory, parts = pending.popleft()
        try:
            with os.scandir(directory) as children:
                for child in children:
                    if entries >= MAX_SCAN_ENTRIES:
                        break
                    entries += 1
                    path = Path(child.path)
                    physical = (len(parts) == 3 and parts[1] == "native-capture"
                                and parts[2].startswith("physical-regression-")
                                and child.name in PHYSICAL_LOG_NAMES)
                    if parts and (child.name in LOG_NAMES or physical) and child.is_file(follow_symlinks=False):
                        if path.resolve().is_relative_to(root):
                            paths.append((child.stat(follow_symlinks=False).st_mtime_ns, path))
                    if len(parts) < 3 or (len(parts) == 3 and parts[1] == "ordinary-evaluation"
                                          and ORDINARY_GROUP.fullmatch(child.name)):
                        if child.is_dir(follow_symlinks=False) and path.resolve() == path:
                            pending.append((path, (*parts, child.name)))
        except OSError:
            continue
    recent = [path for _, path in sorted(paths, reverse=True)]
    existing = [path for path in recent if len(path.relative_to(root).parts) <= 4]
    selected = set(existing[:LEGACY_RUN_SLOTS])
    for path in recent:
        if len(selected) >= MAX_RUNS:
            break
        selected.add(path)
    return tuple(path for path in recent if path in selected)


def events_from(path):
    try:
        if path.resolve() != path:
            return ()
        info = path.stat()
        return read_events(path, info.st_mtime_ns, info.st_size)
    except OSError:
        return ()


@lru_cache(maxsize=12)
def read_events(path, modified_ns, size):
    with path.open("rb") as stream:
        beginning = stream.read(2)
        start = max(0, size - MAX_LOG_BYTES)
        encoding = "utf-16-le" if beginning == b"\xff\xfe" else "utf-8"
        if encoding == "utf-16-le":
            start += start % 2
        stream.seek(start)
        lines = stream.read(size - start).decode(encoding, "replace").splitlines()
    events = deque(maxlen=MAX_LOG_EVENTS)
    for line in lines:
        marker = EVENT_MARKER.search(line)
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
        for key in ("case_id", "id", "finish_reason", "device", "status"):
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
    return tuple(events)


def representative(points):
    if len(points) <= MAX_PACE_POINTS:
        return points
    last = len(points) - 1
    return [points[index * last // (MAX_PACE_POINTS - 1)] for index in range(MAX_PACE_POINTS)]


def capture_pace(captures):
    if captures and all("elapsed_ms" in event for event in captures):
        elapsed = [event["elapsed_ms"] for event in captures]
        if 0 <= elapsed[0] and all(before <= after for before, after in zip(elapsed, elapsed[1:])):
            return [[ms / 1000, event["processed_tokens"]] for ms, event in zip(elapsed, captures)], "elapsed_seconds", "seconds"
    return [[index, event["processed_tokens"]] for index, event in enumerate(captures, 1)], "event_index", "events"


@lru_cache(maxsize=MAX_COMPARISONS)
def read_comparison(path, modified_ns, size):
    if not 0 < size <= MAX_COMPARISON_BYTES:
        return None
    with path.open("rb") as stream:
        raw = stream.read(MAX_COMPARISON_BYTES + 1)
    if len(raw) != size:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        return None
    ident, label = data.get("id"), data.get("label")
    rows, columns = data.get("rows"), data.get("columns")
    ratio, rms = data.get("relative_percent"), data.get("rms")
    if not (isinstance(ident, str) and SAFE_LABEL.fullmatch(ident)
            and isinstance(label, str) and 0 < len(label) <= 300
            and type(rows) is int and type(columns) is int and rows > 0 and columns > 0
            and rows * columns <= MAX_COMPARISON_CELLS
            and type(ratio) in (int, float) and 0 <= ratio <= 1e20
            and isinstance(rms, list) and len(rms) == rows * columns
            and all(type(value) in (int, float) and 0 <= value <= 1e20 for value in rms)):
        return None
    data = {"id": ident, "label": label, "rows": rows, "columns": columns, "relative_percent": ratio, "rms": rms,
            **{key: data[key] for key in ("tensor", "before_sha256", "after_sha256")
               if isinstance(data.get(key), str) and SAFE_LABEL.fullmatch(data[key])}}
    return data


def comparisons():
    names = [CURRENT_WEIGHT, REFERENCE_WEIGHT]
    with os.scandir(HERE) as entries:
        for index, entry in enumerate(entries):
            if index >= MAX_COMPARISONS * 4 or len(names) >= MAX_COMPARISONS:
                break
            if COMPARISON_NAME.fullmatch(entry.name) and entry.name not in names:
                names.append(entry.name)
    result = {}
    for name in names:
        path = HERE / name
        try:
            if path.resolve() == path and path.is_file():
                info = path.stat()
                data = read_comparison(path, info.st_mtime_ns, info.st_size)
                if data is not None:
                    result[name] = data
        except (OSError, ValueError):
            continue
    return result


def comparison_metadata(saved):
    result = []
    seen = set()
    for data in saved.values():
        ident = data["id"]
        if ident in seen:
            continue
        seen.add(ident)
        metadata = {key: data[key] for key in ("id", "label", "rows", "columns", "relative_percent")}
        result.append(dict(metadata, href="/api/weights?" + urlencode({"id": ident})))
    return result


def snapshot(workspace, selection, include_weights=True):
    logs = trace_logs(workspace)
    root = (workspace / "runs").resolve()
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
                and (item.get("case_id") or item.get("id")) == case and "processed_tokens" in item]
    latest = tokens[-1] if tokens else {}
    latest_capture = captures[-1] if captures else {}
    if capture:
        pace, pace_axis, pace_unit = capture_pace(captures)
    else:
        pace = [[item["decode_elapsed_ms"] / 1000, item["step"] + 1] for item in tokens]
        pace_axis, pace_unit = "elapsed_seconds", "seconds"
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
    elif newest.get("event") == "proposal_complete":
        status = "Proposal stopped" if newest.get("status", "").startswith("STOP_") else "Proposal checked"
    elif events:
        status = "Watching" if time.time() - active.stat().st_mtime < 10 else "Last recorded"
    saved = comparisons()
    data = {
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
        "pace": representative(pace),
        "pace_axis": pace_axis,
        "pace_unit": pace_unit,
        "events": stage_events[-22:],
        "comparisons": comparison_metadata(saved),
    }
    if include_weights:
        data.update(weights=saved.get(CURRENT_WEIGHT), reference_weights=saved.get(REFERENCE_WEIGHT))
    return data


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
        if url.path in ASSETS:
            name, mime = ASSETS[url.path]
            path = HERE / name
            if path.resolve() == path and path.is_file():
                self.send(200, mime + "; charset=utf-8", path.read_bytes())
            else:
                self.send(404, "text/plain", b"Not found")
        elif url.path == "/api/live":
            try:
                query = parse_qs(url.query, max_num_fields=12)
                selection = query.get("run", [None])[0]
                include_weights = query.get("weights", ["1"])[0] != "0"
                data = snapshot(self.server.workspace, selection, include_weights)
                self.send_json(data)
            except (OSError, ValueError):
                self.send(503, "application/json", b'{"status":"Waiting for the next complete trace read"}')
        elif url.path == "/api/weights":
            try:
                ident = parse_qs(url.query, max_num_fields=12).get("id", [""])[0]
                data = next((item for item in comparisons().values() if item["id"] == ident), None)
            except (OSError, ValueError):
                data = None
            if data is None:
                self.send(404, "application/json", b'{"status":"Weight comparison not found"}')
            else:
                self.send_json(data)
        else:
            self.send(404, "text/plain", b"Not found")

    def send_json(self, data):
        self.send(200, "application/json", json.dumps(data, allow_nan=False, separators=(",", ":")).encode())


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

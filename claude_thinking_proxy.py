#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude_thinking_proxy.py — Live thinking narration via AIVIS Speech.

Companion to claude_aivis_aloud.py.

# Why this exists

Anthropic's Claude Code 2.1.72+ no longer persists thinking text to
session JSONL files. The `thinking` field is empty; only an opaque
`signature` is stored (Issue anthropics/claude-code#32810). The
JSONL-watching daemon (claude_aivis_aloud.py) can still detect
thinking blocks but has nothing to read out.

The Anthropic streaming API still emits `thinking_delta` events in
plain text. By wrapping the `claude` CLI, capturing its
`--output-format stream-json` output, and tapping thinking_delta events
on the way through, we recover live thinking narration without
modifying Claude Code itself.

# Usage

  python claude_thinking_proxy.py [normal claude args]

Or alias in your shell:
  alias claude='python /path/to/claude_thinking_proxy.py'

# Limitations

- CLI only. Claude Desktop spawns claude.exe via an absolute path
  (e.g. C:\\Users\\<user>\\AppData\\Roaming\\Claude\\claude-code\\<ver>\\claude.exe)
  so PATH-level aliasing does not intercept it. Use claude_aivis_aloud.py
  for Desktop sessions (no thinking, but text + tool_use narration works).

- This proxy ALWAYS runs claude with --output-format stream-json
  --include-partial-messages so it can see thinking_delta events. If you
  invoked with --output-format text, your downstream stdout will see
  stream-json events instead of plain text. For interactive CLI chat,
  this is usually fine; for scripts that parse claude's text output,
  add your own renderer or just use plain `claude`.

- This proxy and the daemon (claude_aivis_aloud.py) post to AIVIS Speech
  independently. Brief audio overlap is possible when thinking and
  normal narration arrive close together. Mitigation in this version:
  thinking is rendered at volume 0.1 so the daemon's louder volume 0.3
  text dominates perceptually.

# Architecture

  parent stdin   →  proxy stdin  →  claude stdin
                                     |
  parent stdout  ←  proxy stdout ←  claude stdout (parsed for thinking_delta)
                                                  |
                                                  → AIVIS /audio_query + /synthesis
                                                  → pygame.mixer playback
"""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import warnings

warnings.filterwarnings("ignore", message=".*pkg_resources.*")

import requests  # noqa: E402

# ---- Config ----
AIVIS_BASE_URL = "http://127.0.0.1:10101"
AIVIS_SPEAKER_ID = 1325133120  # 花音 (Kanon)
THINKING_VOLUME = 0.1   # background-quiet (matches daemon's VOLUME_THINKING)
THINKING_SPEED = 1.1    # slightly faster (matches daemon's NARRATION_SPEED_THINKING)
SYNTH_TIMEOUT_SEC = 15

# Buffer flush rules — keep individual narration chunks listenable.
SENTENCE_END_RE = re.compile(r"[。．！？!?\.\n]")
MIN_FLUSH_CHARS = 40   # don't flush partial fragments shorter than this on a sentence boundary
MAX_BUFFER_CHARS = 200  # force a flush at the latest by this length


def synth_and_play(text: str) -> None:
    """Best-effort one-shot AIVIS synthesis + playback. Errors are swallowed."""
    if not text or not text.strip():
        return
    try:
        q = requests.post(
            f"{AIVIS_BASE_URL}/audio_query",
            params={"speaker": AIVIS_SPEAKER_ID, "text": text},
            timeout=SYNTH_TIMEOUT_SEC,
        )
        if q.status_code != 200:
            return
        audio_query = q.json()
        audio_query["speedScale"] = THINKING_SPEED
        audio_query["volumeScale"] = THINKING_VOLUME
        s = requests.post(
            f"{AIVIS_BASE_URL}/synthesis",
            params={"speaker": AIVIS_SPEAKER_ID},
            json=audio_query,
            timeout=SYNTH_TIMEOUT_SEC,
        )
        if s.status_code != 200:
            return
        # Lazy pygame import: only required when we actually play.
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1)
        pygame.mixer.music.load(io.BytesIO(s.content))
        pygame.mixer.music.play()
        # Block until finished — keeps thinking-deltas from interleaving.
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except (requests.RequestException, OSError):
        pass  # AIVIS down or audio unavailable
    except Exception:
        pass  # any other failure should not break the proxy


class Narrator:
    """Buffers thinking deltas; flushes at sentence boundaries to AIVIS."""

    def __init__(self) -> None:
        self._buf = ""
        self._queue: list[str] = []
        self._lock = threading.Lock()
        self._stop_flag = threading.Event()
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    def feed(self, text: str) -> None:
        if not text:
            return
        with self._lock:
            self._buf += text
            while True:
                m = SENTENCE_END_RE.search(self._buf)
                if m and m.end() >= MIN_FLUSH_CHARS:
                    chunk = self._buf[: m.end()].strip()
                    self._buf = self._buf[m.end():]
                    if chunk:
                        self._queue.append(chunk)
                elif len(self._buf) >= MAX_BUFFER_CHARS:
                    chunk = self._buf.strip()
                    self._buf = ""
                    if chunk:
                        self._queue.append(chunk)
                else:
                    break

    def flush(self) -> None:
        with self._lock:
            if self._buf.strip():
                self._queue.append(self._buf.strip())
                self._buf = ""

    def _loop(self) -> None:
        while not self._stop_flag.is_set():
            with self._lock:
                chunk = self._queue.pop(0) if self._queue else None
            if chunk:
                synth_and_play(chunk)
            else:
                time.sleep(0.05)

    def shutdown(self) -> None:
        self.flush()
        deadline = time.time() + 5.0
        while time.time() < deadline:
            with self._lock:
                empty = not self._queue
            if empty:
                break
            time.sleep(0.1)
        self._stop_flag.set()


def forward_stdin(proc: subprocess.Popen) -> None:
    """Pipe parent stdin → claude stdin verbatim."""
    try:
        for chunk in iter(lambda: sys.stdin.buffer.read1(4096), b""):
            if not chunk:
                break
            proc.stdin.write(chunk)
            proc.stdin.flush()
    except (BrokenPipeError, OSError):
        pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass


def build_claude_args(user_args: list[str]) -> tuple[list[str], bool]:
    """Configure claude invocation for thinking capture.

    `--include-partial-messages` and `--output-format=stream-json` only
    work with `--print` / `-p` (claude --help, 2026-05-10). For interactive
    mode (no --print), we pass args through unchanged — the proxy will
    forward stdout transparently but won't capture thinking deltas.

    Returns (args, capture_enabled).
    """
    args = list(user_args)
    is_print = ("--print" in args) or ("-p" in args)

    if not is_print:
        # Interactive mode — flags would error, just pass through.
        sys.stderr.write(
            "[claude_thinking_proxy] no --print in args; running claude "
            "in pass-through mode (thinking capture disabled)\n"
        )
        return args, False

    if "--output-format" in args:
        idx = args.index("--output-format")
        if idx + 1 < len(args) and args[idx + 1] != "stream-json":
            sys.stderr.write(
                f"[claude_thinking_proxy] overriding --output-format "
                f"{args[idx + 1]} → stream-json (required for thinking capture)\n"
            )
            args[idx + 1] = "stream-json"
    else:
        args = ["--output-format", "stream-json"] + args
    if "--include-partial-messages" not in args:
        args = ["--include-partial-messages"] + args
    return args, True


def resolve_claude_binary() -> str | None:
    """Find the `claude` binary. shutil.which honors PATHEXT on Windows so
    `.cmd`/`.exe` are resolved automatically; falls back to common npm /
    Claude Desktop install paths if the user's PATH does not include them."""
    found = shutil.which("claude")
    if found:
        return found
    import os
    # Common Windows install locations to try as a last resort
    candidates = [
        os.path.expandvars(r"%APPDATA%\npm\claude.cmd"),
        os.path.expandvars(r"%APPDATA%\npm\claude.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def main() -> int:
    args, capture_enabled = build_claude_args(sys.argv[1:])
    claude_bin = resolve_claude_binary()
    if not claude_bin:
        sys.stderr.write(
            "[claude_thinking_proxy] `claude` binary not found on PATH or "
            "in %APPDATA%\\npm. Install Claude Code or adjust PATH.\n"
        )
        return 127
    cmd = [claude_bin] + args
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # share parent stderr
        )
    except FileNotFoundError:
        sys.stderr.write(
            f"[claude_thinking_proxy] resolved binary {claude_bin!r} could "
            f"not be executed.\n"
        )
        return 127

    narrator = Narrator() if capture_enabled else None
    stdin_thread = threading.Thread(target=forward_stdin, args=(proc,), daemon=True)
    stdin_thread.start()

    try:
        for raw_line in iter(proc.stdout.readline, b""):
            # Forward verbatim so downstream consumers see the same stream.
            sys.stdout.buffer.write(raw_line)
            sys.stdout.buffer.flush()
            if narrator is None:
                continue
            try:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("{"):
                    continue
                event = json.loads(line)
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "thinking_delta":
                        narrator.feed(delta.get("thinking", ""))
                elif event.get("type") == "content_block_stop":
                    narrator.flush()
            except json.JSONDecodeError:
                pass  # incomplete or non-JSON line — skip
            except Exception:
                pass  # any other parse failure — skip, keep forwarding
    finally:
        proc.wait()
        if narrator is not None:
            narrator.shutdown()
    return proc.returncode or 0


if __name__ == "__main__":
    sys.exit(main())

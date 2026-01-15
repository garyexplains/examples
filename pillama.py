#!/usr/bin/env python3
"""
Copyright (C) 2026 Gary Sims
All rights reserved.

This program is free software; you can redistribute it and/or modify it
only under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License version 2 for more details.

SPDX-License-Identifier: GPL-2.0-only

---

Streaming chat CLI for a local LLM running on Raspberry Pi AI HAT+ 2
Uses Hailo-Ollama REST API - The Hailo-Ollama API provides a simple
method to run GenAI models on Hailo devices through REST.

See:
https://github.com/hailo-ai/hailo_model_zoo_genai/blob/main/docs/USAGE.rst

The script supports the following endpoints

GET /api/ps - list models that are currently loaded into memory.
GET /hailo/v1/list - list all models available for download.
GET /api/tags - list models already on the server.
DELETE /api/delete - removes a model from local storage
POST /api/show - shows model metadata (parameters, template, details, etc).
POST /api/pull - pulls a model from the library to local storage.
POST /api/chat - chat with the model.

Flags:
--list : list available models
--ps   : list models currently loaded in memory
--pull : pull/download a model (streaming progress)
--model : specify the model to chat with
--tags : list models already on the server
--show : shows model metadata (parameters, template, details, etc)
--delete : Delete a model from local storage
--help : for more info

"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests


def human_bytes(n: Optional[int]) -> str:
    if not isinstance(n, int) or n < 0:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    if i == 0:
        return f"{int(f)} {units[i]}"
    return f"{f:.2f} {units[i]}"


def list_models(list_url: str, timeout: Optional[float] = None) -> int:
    try:
        r = requests.get(list_url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[error] list request failed: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError:
        print("[error] list response was not valid JSON", file=sys.stderr)
        return 2

    models = data.get("models")
    if not isinstance(models, list):
        print("[error] list JSON did not contain a 'models' array", file=sys.stderr)
        return 2

    for m in models:
        print(m)
    return 0


def ps_models(ps_url: str, timeout: Optional[float] = None) -> int:
    """List models currently loaded in memory (/api/ps)."""
    try:
        r = requests.get(ps_url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[error] ps request failed: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError:
        print("[error] ps response was not valid JSON", file=sys.stderr)
        return 2

    models = data.get("models")
    if not isinstance(models, list):
        print("[error] ps JSON did not contain a 'models' array", file=sys.stderr)
        return 2

    if not models:
        print("(no models loaded)")
        return 0

    # Compact, readable output without extra deps.
    for m in models:
        if not isinstance(m, dict):
            print(m)
            continue
        name = m.get("name") or m.get("model") or "?"
        size = human_bytes(m.get("size")) if "size" in m else "?"
        modified_at = m.get("modified_at", "?")
        expires_at = m.get("expires_at", "?")
        details = m.get("details") or {}
        family = details.get("family", "?")
        params = details.get("parameter_size", "?")
        quant = details.get("quantization_level", "?")
        fmt = details.get("format", "?")

        print(f"{name}")
        print(f"  size: {size}")
        print(f"  modified_at: {modified_at}")
        print(f"  expires_at:  {expires_at}")
        print(f"  details: family={family}, params={params}, quant={quant}, format={fmt}")
    return 0

def tags_models(tags_url: str, timeout: Optional[float] = None) -> int:
    """List models already on the server (/api/tags)."""
    try:
        r = requests.get(tags_url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[error] tags request failed: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError:
        print("[error] tags response was not valid JSON", file=sys.stderr)
        return 2

    models = data.get("models")
    if not isinstance(models, list):
        print("[error] tags JSON did not contain a 'models' array", file=sys.stderr)
        return 2

    if not models:
        print("(no models on server)")
        return 0

    for m in models:
        if not isinstance(m, dict):
            print(m)
            continue

        name = m.get("name") or m.get("model") or "?"
        size = human_bytes(m.get("size")) if "size" in m else "?"
        modified_at = m.get("modified_at", "?")
        details = m.get("details") or {}
        family = details.get("family", "?")
        params = details.get("parameter_size", "?")
        quant = details.get("quantization_level", "?")
        fmt = details.get("format", "?")

        print(f"{name}")
        print(f"  size: {size}")
        print(f"  modified_at: {modified_at}")
        print(f"  details: family={family}, params={params}, quant={quant}, format={fmt}")

    return 0

def show_model(show_url: str, model: str, timeout: Optional[float] = None) -> int:
    """Show model metadata (/api/show)."""
    payload = {"model": model}

    try:
        r = requests.post(show_url, json=payload, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[error] show request failed: {e}", file=sys.stderr)
        return 2

    # Some servers may still send {"error": "..."} with 200
    try:
        data = r.json()
    except json.JSONDecodeError:
        print("[error] show response was not valid JSON", file=sys.stderr)
        return 2

    if isinstance(data, dict) and "error" in data:
        print(f"[error] {data.get('error')}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print(data)
        return 0

    # Pretty print important fields
    print(f"model: {model}")
    if "modified_at" in data:
        print(f"modified_at: {data.get('modified_at')}")

    details = data.get("details") or {}
    if isinstance(details, dict) and details:
        family = details.get("family", "?")
        params = details.get("parameter_size", "?")
        quant = details.get("quantization_level", "?")
        fmt = details.get("format", "?")
        parent = details.get("parent_model", "")
        print("details:")
        print(f"  family: {family}")
        print(f"  parameter_size: {params}")
        print(f"  quantization_level: {quant}")
        print(f"  format: {fmt}")
        if parent:
            print(f"  parent_model: {parent}")

    # Show these verbatim (they can be multi-line / large)
    for key in ("license", "modelfile", "parameters", "template", "model_info"):
        if key in data:
            val = data.get(key)
            if val:
                print(f"\n{key}:\n{val}")
            else:
                print(f"\n{key}: (empty)")

    # Print any extra keys not covered above (so you don't miss new fields)
    known = {"license", "modelfile", "parameters", "template", "details", "model_info", "modified_at"}
    extras = {k: v for k, v in data.items() if k not in known}
    if extras:
        print("\nother_fields:")
        for k, v in extras.items():
            print(f"  {k}: {v}")

    return 0


def pull_model(pull_url: str, model: str, timeout: Optional[float] = None) -> int:
    payload = {"model": model, "stream": True}

    saw_success = False
    saw_progress = False
    last_line_len = 0
    buf = b""  # bytes buffer

    def end_progress_line():
        nonlocal saw_progress, last_line_len
        if saw_progress:
            print()
            saw_progress = False
            last_line_len = 0

    def handle_obj(obj: Dict[str, Any]) -> Optional[int]:
        nonlocal saw_success, saw_progress, last_line_len

        status = obj.get("status", "")
        total = obj.get("total")
        completed = obj.get("completed")

        if status == "pulling" and isinstance(total, int) and isinstance(completed, int) and total > 0:
            saw_progress = True
            pct = (completed / total) * 100.0
            line = f"{status}: {pct:6.2f}%  ({human_bytes(completed)} / {human_bytes(total)})"
            pad = max(0, last_line_len - len(line))
            print("\r" + line + (" " * pad), end="", flush=True)
            last_line_len = len(line)
            return None

        end_progress_line()

        if status:
            print(status)
        else:
            print(obj)

        if status == "success":
            saw_success = True
            return 0

        return None

    def process_line_bytes(line_b: bytes) -> Optional[int]:
        line_b = line_b.strip()
        if not line_b:
            return None
        try:
            line = line_b.decode("utf-8", errors="replace")
            obj = json.loads(line)
        except json.JSONDecodeError:
            end_progress_line()
            print(f"[warn] non-JSON line: {line_b[:200]!r}", file=sys.stderr)
            return None
        return handle_obj(obj)

    try:
        with requests.post(pull_url, json=payload, stream=True, timeout=timeout) as r:
            r.raise_for_status()

            try:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    buf += chunk
                    while b"\n" in buf:
                        line_b, buf = buf.split(b"\n", 1)
                        rc = process_line_bytes(line_b)
                        if rc is not None:
                            return rc
            except requests.exceptions.RequestException:
                # Connection broke mid-stream; still parse buffered data below.
                pass

            if buf.strip():
                for line_b in buf.splitlines():
                    rc = process_line_bytes(line_b)
                    if rc is not None:
                        return rc

            return 0 if saw_success else 1

    except requests.exceptions.RequestException as e:
        if saw_success:
            return 0
        end_progress_line()
        print(f"[error] pull request failed: {e}", file=sys.stderr)
        return 2


def delete_model(delete_url: str, model: str, timeout: Optional[float] = None) -> int:
    """Delete a model from local storage (/api/delete). Server may return an empty body."""
    payload = {"model": model}
    try:
        r = requests.request("DELETE", delete_url, json=payload, timeout=timeout)

        # If server uses proper HTTP error codes
        if r.status_code >= 400:
            # Try to show JSON error if present
            try:
                data = r.json()
                if isinstance(data, dict) and "error" in data:
                    print(f"[error] {data['error']}", file=sys.stderr)
                else:
                    print(f"[error] delete failed: HTTP {r.status_code}", file=sys.stderr)
            except Exception:
                print(f"[error] delete failed: HTTP {r.status_code}", file=sys.stderr)
            return 2

        # Success with empty body is fine (common: 200/204)
        if r.content:
            # If a body exists, show error if it contains one
            try:
                data = r.json()
                if isinstance(data, dict) and "error" in data:
                    print(f"[error] {data['error']}", file=sys.stderr)
                    return 2
            except Exception:
                pass

        print(f"Deleted model: {model}")
        return 0

    except requests.RequestException as e:
        print(f"[error] delete request failed: {e}", file=sys.stderr)
        return 2

def stream_chat(chat_url: str, model: str, user_text: str, timeout: Optional[float] = None) -> None:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_text}],
    }

    with requests.post(chat_url, json=payload, stream=True, timeout=timeout) as r:
        r.raise_for_status()

        total_duration = None
        eval_count = None
        printed_any = False

        for raw_line in r.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            try:
                obj: Dict[str, Any] = json.loads(raw_line)
            except json.JSONDecodeError:
                print(f"\n[warn] non-JSON line: {raw_line}", file=sys.stderr)
                continue

            # Server-side error payload (may still be HTTP 200)
            if "error" in obj:
                err = obj.get("error")
                print(f"[error] {err}", file=sys.stderr)
                return

            msg = obj.get("message") or {}
            chunk = msg.get("content")
            if chunk:
                printed_any = True
                print(chunk, end="", flush=True)

            if obj.get("done") is True:
                total_duration = obj.get("total_duration", total_duration)
                eval_count = obj.get("eval_count", eval_count)
                break

        if printed_any:
            print()  # newline after assistant response

        # Summary: seconds, tokens, token rate
        secs = None
        if isinstance(total_duration, (int, float)):
            secs = total_duration / 1_000_000_000

        parts = []
        if secs is not None:
            parts.append(f"time={secs:.3f}s")
        if eval_count is not None:
            parts.append(f"tokens={eval_count}")
            if secs and secs > 0:
                parts.append(f"rate={eval_count / secs:.2f} tok/s")

        if parts:
            print("[" + ", ".join(parts) + "]")


def main() -> int:
    p = argparse.ArgumentParser(description="Streaming chat CLI for a local LLM running on Raspberry Pi AI HAT+ 2")
    p.add_argument("--model", help="Model name, e.g. qwen2:1.5b (required unless --list, --ps, --tags, --pull, --show, or --delete is used)")
    p.add_argument(
        "--chat-url",
        default="http://localhost:8000/api/chat",
        help="Chat endpoint URL (default: http://localhost:8000/api/chat)",
    )

    p.add_argument("--list", action="store_true", help="List available models and exit")
    p.add_argument(
        "--list-url",
        default="http://localhost:8000/hailo/v1/list",
        help="List-models endpoint URL (default: http://localhost:8000/hailo/v1/list)",
    )

    p.add_argument("--ps", action="store_true", help="List currently loaded models and exit")
    p.add_argument(
        "--ps-url",
        default="http://localhost:8000/api/ps",
        help="Loaded-models endpoint URL (default: http://localhost:8000/api/ps)",
    )

    p.add_argument("--tags", action="store_true", help="List models already on the server and exit")
    p.add_argument(
        "--tags-url",
        default="http://localhost:8000/api/tags",
        help="Tags endpoint URL (default: http://localhost:8000/api/tags)",
    )

    p.add_argument("--show", metavar="MODEL", help="Show model metadata and exit")
    p.add_argument(
        "--show-url",
        default="http://localhost:8000/api/show",
        help="Show endpoint URL (default: http://localhost:8000/api/show)",
    )

    p.add_argument("--pull", metavar="MODEL", help="Pull/download a model (streaming progress) and exit")
    p.add_argument(
        "--pull-url",
        default="http://localhost:8000/api/pull",
        help="Pull endpoint URL (default: http://localhost:8000/api/pull)",
    )

    p.add_argument("--delete", metavar="MODEL", help="Delete a model from local storage and exit")
    p.add_argument(
        "--delete-url",
        default="http://localhost:8000/api/delete",
        help="Delete endpoint URL (default: http://localhost:8000/api/delete)",
    )

    p.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Optional requests timeout in seconds (default: no timeout)",
    )
    args = p.parse_args()

    if args.list:
        return list_models(args.list_url, timeout=args.timeout)

    if args.ps:
        return ps_models(args.ps_url, timeout=args.timeout)

    if args.show:
        return show_model(args.show_url, args.show, timeout=args.timeout)

    if args.tags:
        return tags_models(args.tags_url, timeout=args.timeout)

    if args.pull:
        print(f"Pulling model: {args.pull}")
        return pull_model(args.pull_url, args.pull, timeout=args.timeout)

    if args.delete:
        print(f"Deleting model: {args.delete}")
        return delete_model(args.delete_url, args.delete, timeout=args.timeout)

    if not args.model:
        p.error("--model is required unless --list, --ps, --tags, --pull, --show, or --delete is used")

    print(f"Using model: {args.model}")
    print("Type your prompt. Press Enter to send. Type /exit or Ctrl-D to quit.\n")

    while True:
        try:
            user_text = input("> ").strip()
        except EOFError:
            print()
            return 0

        if not user_text:
            continue
        if user_text.lower() in {"/exit", "/quit"}:
            return 0

        try:
            stream_chat(args.chat_url, args.model, user_text, timeout=args.timeout)
        except requests.RequestException as e:
            print(f"[error] request failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

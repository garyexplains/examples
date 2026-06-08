#!/usr/bin/env python3
"""
Ask a local Ollama model about a Markdown file.

Usage:
    python askai.py aapl_news.md
    python askai.py aapl_news.md --question "Summarize the biggest risks."
    python askai.py aapl_news.md --model llama3.1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_QUESTION = "tell me the financial situation of the company based on this data"
DEFAULT_MODEL = "gemma4:e4b"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"


def build_prompt(markdown: str, question: str) -> str:
    return f"""Use the following Markdown data to answer the question.

Markdown data:
{markdown}

Question:
{question}
"""


def ask_ollama(url: str, model: str, prompt: str) -> str:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")

    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return str(payload.get("response", "")).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown_file", help="Path to the Markdown file to send to Ollama.")
    parser.add_argument(
        "--question",
        default=DEFAULT_QUESTION,
        help=f"Question to ask. Default: {DEFAULT_QUESTION!r}",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name. Default: {DEFAULT_MODEL}")
    parser.add_argument(
        "--url",
        default=DEFAULT_OLLAMA_URL,
        help=f"Ollama generate endpoint. Default: {DEFAULT_OLLAMA_URL}",
    )
    args = parser.parse_args()

    markdown_path = Path(args.markdown_file)
    if not markdown_path.exists():
        print(f"Markdown file not found: {markdown_path}", file=sys.stderr)
        return 1

    markdown = markdown_path.read_text(encoding="utf-8")
    prompt = build_prompt(markdown, args.question)

    try:
        answer = ask_ollama(args.url, args.model, prompt)
    except HTTPError as exc:
        print(f"Ollama HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Could not connect to Ollama: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("Timed out waiting for Ollama.", file=sys.stderr)
        return 1

    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

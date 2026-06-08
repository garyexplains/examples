#!/usr/bin/env python3
"""
Scrape Google Finance news articles into one Markdown file using Decodo.

Set your Decodo Basic auth token in DECODO_AUTH_TOKEN, or pass it with --auth.
Use either the Base64 value from Decodo's examples or username:password.

Usage:
    python scrape_google_finance_decodo.py
    python scrape_google_finance_decodo.py --output aapl_news.md
    python scrape_google_finance_decodo.py --auth YOUR_BASE64_TOKEN --output aapl_news.md
    python scrape_google_finance_decodo.py https://www.google.com/finance/quote/MSFT:NASDAQ --output msft_news.md
"""

from __future__ import annotations

import base64
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from requests import PreparedRequest
from bs4 import BeautifulSoup

from scrape_google_finance import (
    DEFAULT_QUOTE_URL,
    article_paragraphs_from_soup,
    article_title_from_soup,
    default_output_path,
    scrape_news_links_from_soup,
    write_markdown,
)


DECODO_SCRAPE_URL = "https://scraper-api.decodo.com/v2/scrape"


def debug_log(enabled: bool, message: str) -> None:
    if enabled:
        stamp = datetime.now().isoformat(timespec="seconds")
        print(f"[{stamp}] {message}", file=sys.stderr, flush=True)


def format_prepared_request(request: PreparedRequest | None) -> str:
    if request is None:
        return "No prepared request was available from the Decodo response."

    lines = [
        "----- Decodo request debug -----",
        f"{request.method} {request.url}",
        "",
        "Headers:",
    ]
    for key, value in request.headers.items():
        lines.append(f"{key}: {value}")

    lines.extend(["", "Body:"])
    body: Any = request.body
    if isinstance(body, bytes):
        lines.append(body.decode("utf-8", errors="replace"))
    elif body is None:
        lines.append("")
    else:
        lines.append(str(body))

    lines.append("----- End Decodo request debug -----")
    return "\n".join(lines)


def auth_header_value(auth: str | None, username: str | None, password: str | None) -> str:
    if username and password:
        raw = f"{username}:{password}"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return f"Basic {encoded}"

    if not auth:
        raise ValueError("Missing Decodo credentials.")

    auth = auth.strip()
    if auth.lower().startswith("basic "):
        return auth
    if ":" in auth:
        encoded = base64.b64encode(auth.encode("utf-8")).decode("ascii")
        return f"Basic {encoded}"
    return f"Basic {auth}"


def decodo_fetch_html(
    target_url: str,
    authorization: str,
    decodo_url: str = DECODO_SCRAPE_URL,
    headless: str = "html",
    timeout: int = 120,
    debug: bool = False,
) -> str:
    debug_log(debug, f"Decodo request starting: {target_url}")
    response = requests.post(
        decodo_url,
        json={"url": target_url, "proxy_pool": "premium", "device_type": "desktop_chrome", "headless": headless},
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": authorization,
        },
        timeout=timeout,
    )
    debug_log(debug, f"Decodo response received: status={response.status_code} url={target_url}")
    response.raise_for_status()

    payload = response.json()
    try:
        content = str(payload["results"][0]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Decodo response shape: {payload}") from exc
    debug_log(debug, f"Decodo content extracted: {len(content):,} characters from {target_url}")
    return content


def soup_from_decodo(target_url: str, authorization: str, headless: str, timeout: int, debug: bool) -> BeautifulSoup:
    html = decodo_fetch_html(
        target_url,
        authorization=authorization,
        headless=headless,
        timeout=timeout,
        debug=debug,
    )
    debug_log(debug, f"Parsing HTML with Beautiful Soup: {target_url}")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style", "noscript", "svg", "nav", "footer", "aside", "form"]):
        tag.decompose()
    debug_log(debug, f"Finished parsing HTML: {target_url}")
    return soup


def scrape_news_links(
    quote_url: str,
    authorization: str,
    headless: str,
    timeout: int,
    debug: bool,
) -> list[dict[str, str]]:
    debug_log(debug, f"Fetching Google Finance quote page: {quote_url}")
    soup = soup_from_decodo(quote_url, authorization, headless, timeout, debug)
    debug_log(debug, "Extracting news links from Google Finance page")
    stories = scrape_news_links_from_soup(soup)
    debug_log(debug, f"Found {len(stories)} news story links")
    for index, story in enumerate(stories, start=1):
        debug_log(debug, f"Story {index}: {story['title']} -> {story['url']}")
    return stories


def scrape_article(
    story: dict[str, str],
    authorization: str,
    headless: str,
    timeout: int,
    debug: bool,
    index: int,
    total: int,
) -> dict[str, object]:
    debug_log(debug, f"Article {index}/{total} starting: {story['title']}")
    debug_log(debug, f"Article {index}/{total} URL: {story['url']}")
    try:
        soup = soup_from_decodo(story["url"], authorization, headless, timeout, debug)
    except (requests.RequestException, RuntimeError) as exc:
        debug_log(debug, f"Article {index}/{total} failed: {exc}")
        return {**story, "paragraphs": [], "error": str(exc)}

    debug_log(debug, f"Article {index}/{total} extracting title and paragraphs")
    paragraphs = article_paragraphs_from_soup(soup)
    debug_log(debug, f"Article {index}/{total} extracted {len(paragraphs)} paragraphs")
    return {
        **story,
        "title": article_title_from_soup(soup, story["title"]),
        "paragraphs": paragraphs,
        "error": None if paragraphs else "No article text found",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("quote_url", nargs="?", default=DEFAULT_QUOTE_URL)
    parser.add_argument("--output", help="Markdown output file.")
    parser.add_argument(
        "--auth",
        default=os.environ.get("DECODO_AUTH_TOKEN"),
        help="Decodo Basic auth token, full 'Basic ...' header value, or username:password. Defaults to DECODO_AUTH_TOKEN.",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("DECODO_USERNAME"),
        help="Decodo username. Defaults to DECODO_USERNAME.",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("DECODO_PASSWORD"),
        help="Decodo password. Defaults to DECODO_PASSWORD.",
    )
    parser.add_argument(
        "--headless",
        default="html",
        help='Decodo headless mode. Default: "html".',
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds for each Decodo request. Default: 120.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print progress messages while scraping.",
    )
    args = parser.parse_args()

    debug_log(args.debug, "Starting Decodo Google Finance scraper")
    debug_log(args.debug, f"Quote URL: {args.quote_url}")
    debug_log(args.debug, f"Headless mode: {args.headless}")
    debug_log(args.debug, f"Request timeout: {args.timeout} seconds")

    try:
        authorization = auth_header_value(args.auth, args.username, args.password)
    except ValueError:
        print(
            "Missing Decodo credentials. Set DECODO_AUTH_TOKEN, pass --auth, or set DECODO_USERNAME and DECODO_PASSWORD.",
            file=sys.stderr,
        )
        return 1
    debug_log(args.debug, "Decodo authorization header prepared")

    try:
        stories = scrape_news_links(args.quote_url, authorization, args.headless, args.timeout, args.debug)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 401:
            print(
                "Decodo returned 401 Unauthorized. Check that your Decodo credentials are correct and active. "
                "Use --auth with the Base64 token from Decodo, --auth username:password, or --username/--password.",
                file=sys.stderr,
            )
            print(format_prepared_request(exc.response.request), file=sys.stderr)
        else:
            print(f"Could not fetch Google Finance page with Decodo: {exc}", file=sys.stderr)
        return 1
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Could not fetch Google Finance page with Decodo: {exc}", file=sys.stderr)
        return 1

    articles = [
        scrape_article(story, authorization, args.headless, args.timeout, args.debug, index, len(stories))
        for index, story in enumerate(stories, start=1)
    ]
    output_path = Path(args.output) if args.output else default_output_path(args.quote_url)
    debug_log(args.debug, f"Writing Markdown output: {output_path}")
    write_markdown(articles, output_path, args.quote_url)
    debug_log(args.debug, "Finished writing Markdown output")

    print(f"Wrote {len(articles)} articles to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Scrape Google Finance news articles into one Markdown file.

Usage:
    python scrape_google_finance.py
    python scrape_google_finance.py --output aapl_news.md
    python scrape_google_finance.py https://www.google.com/finance/quote/MSFT:NASDAQ --output msft_news.md
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError:
    print("Install Beautiful Soup first: pip install beautifulsoup4", file=sys.stderr)
    raise SystemExit(1)


DEFAULT_QUOTE_URL = "https://www.google.com/finance/quote/AAPL:NASDAQ"
GOOGLE_FINANCE_URL = "https://www.google.com/finance/"
SKIP_TAGS = ["script", "style", "noscript", "svg", "nav", "footer", "aside", "form"]


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def soup_from_url(url: str) -> BeautifulSoup:
    soup = BeautifulSoup(fetch_html(url), "html.parser")
    for tag in soup.find_all(SKIP_TAGS):
        tag.decompose()
    return soup


def clean_text(value: str | None) -> str:
    return " ".join(unescape(value or "").split())


def clean_google_redirect(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [""])[0]
        if target:
            return unquote(target)
    return url


def is_external_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and not parsed.netloc.endswith("google.com")


def is_news_heading(node: object) -> bool:
    return isinstance(node, NavigableString) and clean_text(str(node)) == "News stories"


def external_links(tag: Tag | BeautifulSoup) -> list[Tag]:
    links: list[Tag] = []
    for link in tag.find_all("a", href=True):
        url = clean_google_redirect(urljoin(GOOGLE_FINANCE_URL, str(link["href"])))
        title = clean_text(link.get_text(" ", strip=True))
        if title and is_external_url(url):
            links.append(link)
    return links


def find_news_container(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    heading = soup.find(string=is_news_heading)
    if not heading or not isinstance(heading.parent, Tag):
        return soup

    current: Tag | None = heading.parent
    while current:
        if len(external_links(current)) >= 2:
            return current
        current = current.parent if isinstance(current.parent, Tag) else None

    return heading.parent


def scrape_news_links_from_soup(soup: BeautifulSoup) -> list[dict[str, str]]:
    container = find_news_container(soup)

    stories: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for link in external_links(container):
        text_seen_before_link = clean_text(" ".join(link.find_all_previous(string=True)))
        if "Profile" in text_seen_before_link:
            break

        url = clean_google_redirect(urljoin(GOOGLE_FINANCE_URL, str(link["href"])))
        if url in seen_urls:
            continue
        seen_urls.add(url)

        stories.append(
            {
                "title": clean_text(link.get_text(" ", strip=True)),
                "url": url,
            }
        )

    return stories


def scrape_news_links(quote_url: str) -> list[dict[str, str]]:
    return scrape_news_links_from_soup(soup_from_url(quote_url))


def meta_content(soup: BeautifulSoup, *keys: str) -> str | None:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return clean_text(str(tag["content"]))
    return None


def is_article_text(text: str) -> bool:
    if len(text) < 40:
        return False
    lower = text.lower()
    skip_phrases = [
        "all rights reserved",
        "cookie",
        "privacy policy",
        "terms of service",
        "subscribe",
        "advertisement",
        "enable javascript",
    ]
    return not any(phrase in lower for phrase in skip_phrases)


def unique_texts(texts: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for text in texts:
        key = re.sub(r"\W+", "", text.lower())
        if key not in seen:
            seen.add(key)
            result.append(text)
    return result


def article_title_from_soup(soup: BeautifulSoup, fallback_title: str) -> str:
    title = meta_content(soup, "og:title", "twitter:title")
    if not title and soup.title:
        title = clean_text(soup.title.get_text(" ", strip=True))
    title = title or fallback_title
    return re.sub(r"\s+[-|]\s+.*$", "", title).strip() or title


def article_paragraphs_from_soup(soup: BeautifulSoup) -> list[str]:
    root = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = [
        clean_text(tag.get_text(" ", strip=True))
        for tag in root.find_all(["p", "blockquote", "li"])
    ]
    paragraphs = unique_texts([text for text in paragraphs if is_article_text(text)])

    description = meta_content(soup, "description", "og:description", "twitter:description")
    if description and description not in paragraphs:
        paragraphs.insert(0, description)

    return paragraphs


def scrape_article(story: dict[str, str]) -> dict[str, object]:
    try:
        soup = soup_from_url(story["url"])
    except (HTTPError, URLError, TimeoutError) as exc:
        return {**story, "paragraphs": [], "error": str(exc)}

    paragraphs = article_paragraphs_from_soup(soup)
    return {
        **story,
        "title": article_title_from_soup(soup, story["title"]),
        "paragraphs": paragraphs,
        "error": None if paragraphs else "No article text found",
    }


def default_output_path(quote_url: str) -> Path:
    match = re.search(r"/quote/([^:/?#]+):([^/?#]+)", urlparse(quote_url).path)
    label = f"{match.group(1)}_{match.group(2)}" if match else "quote"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"google_finance_news_{label}_{stamp}.md")


def write_markdown(articles: list[dict[str, object]], output_path: Path, quote_url: str) -> None:
    lines = [
        "# Google Finance News Articles",
        "",
        f"Source quote page: {quote_url}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    for index, article in enumerate(articles, start=1):
        lines.extend(["---", "", f"## {index}. {article['title']}", "", f"URL: {article['url']}", ""])

        if article.get("error"):
            lines.extend([f"_Could not extract article text: {article['error']}_", ""])
            continue

        for paragraph in article["paragraphs"]:
            lines.extend([str(paragraph), ""])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("quote_url", nargs="?", default=DEFAULT_QUOTE_URL)
    parser.add_argument("--output", help="Markdown output file.")
    args = parser.parse_args()

    try:
        stories = scrape_news_links(args.quote_url)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Could not fetch Google Finance page: {exc}", file=sys.stderr)
        return 1

    articles = [scrape_article(story) for story in stories]
    output_path = Path(args.output) if args.output else default_output_path(args.quote_url)
    write_markdown(articles, output_path, args.quote_url)

    print(f"Wrote {len(articles)} articles to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

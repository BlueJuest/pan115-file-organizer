import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import parse_qs, quote, unquote, urlparse

import httpx


@dataclass(slots=True)
class DoubanMatch:
    rating: str
    url: str


class DoubanClient:
    def __init__(self) -> None:
        self.client = httpx.Client(
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Safari/537.36",
            },
        )

    def search(self, title: str, year: int | None = None) -> DoubanMatch | None:
        response = self.client.get(f"https://www.douban.com/search?cat=1002&q={quote(title)}")
        response.raise_for_status()
        return self.parse_search_html(response.text, title, year)

    def parse_search_html(self, html: str, title: str, year: int | None = None) -> DoubanMatch | None:
        blocks = re.findall(r'<div class="result"[\s\S]*?</div>\s*</div>', html)
        if not blocks:
            blocks = [html]
        for block in blocks:
            url = self._extract_subject_url(block)
            rating_match = re.search(r'<span class="rating_nums">([^<]+)</span>', block)
            plain = re.sub(r"<[^>]+>", " ", unescape(block))
            if title and title not in plain:
                continue
            if year is not None and str(year) not in plain:
                continue
            if url:
                rating = f"{rating_match.group(1).strip()}/10" if rating_match else ""
                return DoubanMatch(rating=rating, url=url)
        return None

    def _extract_subject_url(self, html: str) -> str:
        direct_match = re.search(r'https://movie\.douban\.com/subject/\d+/?', html)
        if direct_match:
            return direct_match.group(0)
        for encoded in re.findall(r'url=([^&"\']+)', unescape(html)):
            decoded = unquote(encoded)
            if re.match(r'https://movie\.douban\.com/subject/\d+/?$', decoded):
                return decoded
        for href in re.findall(r'href="([^"]+)"', unescape(html)):
            parsed = urlparse(href)
            target = parse_qs(parsed.query).get("url", [""])[0]
            if re.match(r'https://movie\.douban\.com/subject/\d+/?$', target):
                return target
        return ""

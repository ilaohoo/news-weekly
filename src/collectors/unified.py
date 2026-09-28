"""统一采集器：读 sources.py 配置，自动执行 RSS 优先 + 爬虫兜底。"""
from typing import List

import feedparser
import requests
from bs4 import BeautifulSoup

from src.config import MAX_ITEMS_PER_SOURCE
from src.models import NewsItem
from src.sources import SourceConfig

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class UnifiedCollector:
    def __init__(self, cfg: SourceConfig):
        self.cfg = cfg
        self.name = cfg["name"]

    def collect(self) -> List[NewsItem]:
        if self.cfg.get("custom_crawl"):
            try:
                items = self.cfg["custom_crawl"](self)
                if items:
                    return items[:MAX_ITEMS_PER_SOURCE]
            except Exception as e:
                print(f"[{self.name}] 自定义采集失败: {e}")

        for url in self.cfg.get("rss_urls", []):
            try:
                items = self._from_rss(url)
                if items:
                    print(f"[{self.name}] RSS 成功: {url} ({len(items)} 条)")
                    return items[:MAX_ITEMS_PER_SOURCE]
            except Exception as e:
                print(f"[{self.name}] RSS 失败 {url}: {e}")

        if self.cfg.get("crawl_url"):
            try:
                items = self._from_crawl()
                if items:
                    print(f"[{self.name}] 爬虫成功 ({len(items)} 条)")
                    return items[:MAX_ITEMS_PER_SOURCE]
            except Exception as e:
                print(f"[{self.name}] 爬虫失败: {e}")

        print(f"[{self.name}] 所有方式均失败")
        return []

    def _from_rss(self, url: str) -> List[NewsItem]:
        feed = feedparser.parse(url)
        out: List[NewsItem] = []
        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            summary = self._strip(entry.get("summary") or entry.get("description") or "")
            pub = entry.get("published") or entry.get("updated") or ""
            out.append(NewsItem(
                title=title, url=link, source=self.name,
                summary=summary[:300], published=pub,
            ))
        return out

    def _from_crawl(self) -> List[NewsItem]:
        base_url = self.cfg["crawl_url"]
        domain = self.cfg["domain"]
        out: List[NewsItem] = []
        resp = self._get(base_url)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        seen = set()
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            href = a["href"].strip()
            if len(title) < 8:
                continue
            if href.startswith("//"):
                href = "http:" + href
            elif href.startswith("/"):
                href = base_url.rstrip("/") + href
            if not href.startswith("http") or domain not in href:
                continue
            if href in seen:
                continue
            seen.add(href)
            out.append(NewsItem(title=title, url=href, source=self.name))
        return out

    @staticmethod
    def _strip(html: str) -> str:
        return BeautifulSoup(html or "", "lxml").get_text(strip=True)

    @staticmethod
    def _get(url: str) -> requests.Response:
        return requests.get(url, headers=HEADERS, timeout=15)


def build_collectors() -> List[UnifiedCollector]:
    from src.sources import SOURCES
    return [UnifiedCollector(cfg) for cfg in sorted(SOURCES, key=lambda x: x["priority"])]

"""所有新闻源的集中配置。

添加新新闻源只需在 SOURCES 列表里加一条 dict 即可。
"""
from typing import Callable, List, Optional, TypedDict

from src.models import NewsItem


class SourceConfig(TypedDict, total=False):
    name: str
    priority: int
    rss_urls: List[str]
    crawl_url: str
    domain: str
    custom_crawl: Optional[Callable]


def _zhihu_crawl(collector) -> List[NewsItem]:
    """知乎热榜的特殊处理（无 RSS，走公开 API）。"""
    out: List[NewsItem] = []
    try:
        resp = collector._get(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
        )
        data = resp.json()
        for entry in data.get("data", []):
            target = entry.get("target", {})
            title = (target.get("title") or "").strip()
            url = target.get("url", "")
            if url and "/api/v4/questions/" in url:
                qid = url.split("/")[-1]
                url = f"https://www.zhihu.com/question/{qid}"
            if not title or not url:
                continue
            out.append(NewsItem(
                title=title, url=url, source="知乎热点",
                summary=(target.get("excerpt") or "")[:300],
            ))
    except Exception as e:
        print(f"[知乎热点] 接口失败: {e}")
    return out


SOURCES: List[SourceConfig] = [
    # ===== 核心时政源 =====
    {
        "name": "新华网",
        "priority": 1,
        "rss_urls": [
            "http://www.xinhuanet.com/politics/news_politics.xml",
            "http://www.xinhuanet.com/world/news_world.xml",
            "http://www.xinhuanet.com/tech/news_tech.xml",
        ],
        "crawl_url": "http://www.news.cn/",
        "domain": "news.cn",
    },
    {
        "name": "人民网",
        "priority": 2,
        "rss_urls": [
            "http://www.people.com.cn/rss/politics.xml",
            "http://www.people.com.cn/rss/world.xml",
        ],
        "crawl_url": "http://www.people.com.cn/",
        "domain": "people.com.cn",
    },
    {
        "name": "参考消息",
        "priority": 3,
        "rss_urls": [
            "http://www.cankaoxiaoxi.com/rss.xml",
        ],
        "crawl_url": "http://www.cankaoxiaoxi.com/",
        "domain": "cankaoxiaoxi.com",
    },
    # ===== 综合门户 =====
    {
        "name": "新浪",
        "priority": 4,
        "rss_urls": [
            "http://rss.sina.com.cn/news/china/focus15.xml",
            "http://rss.sina.com.cn/news/world/focus15.xml",
        ],
        "crawl_url": "https://news.sina.com.cn/",
        "domain": "sina.com.cn",
    },
    {
        "name": "搜狐",
        "priority": 5,
        "rss_urls": [
            "http://rss.news.sohu.com/rss/guonei.xml",
            "http://rss.news.sohu.com/rss/guoji.xml",
        ],
        "crawl_url": "https://news.sohu.com/",
        "domain": "sohu.com",
    },
    {
        "name": "网易",
        "priority": 6,
        "rss_urls": [
            "https://news.163.com/special/00011K6L/rss_newstop.xml",
        ],
        "crawl_url": "https://news.163.com/",
        "domain": "163.com",
    },
    {
        "name": "凤凰网",
        "priority": 7,
        "rss_urls": [
            "https://news.ifeng.com/rss/index.xml",
        ],
        "crawl_url": "https://news.ifeng.com/",
        "domain": "ifeng.com",
    },
    # ===== 青少年 / 教育 / 体育 / 科普 / 人物 专属源 =====
    {
        "name": "未来网",
        "priority": 1,   # 青少年专属，与新华网同级
        "rss_urls": [],
        "crawl_url": "http://www.k618.cn/",
        "domain": "k618.cn",
    },
    {
        "name": "中国教育新闻网",
        "priority": 2,
        "rss_urls": [],
        "crawl_url": "http://www.jyb.cn/",
        "domain": "jyb.cn",
    },
    {
        "name": "中国科普网",
        "priority": 2,
        "rss_urls": [],
        "crawl_url": "http://www.kepu.gov.cn/",
        "domain": "kepu.gov.cn",
    },
    {
        "name": "华奥星空",
        "priority": 3,
        "rss_urls": [],
        "crawl_url": "http://www.sports.cn/",
        "domain": "sports.cn",
    },
    {
        "name": "中国青年网",
        "priority": 3,
        "rss_urls": [],
        "crawl_url": "http://www.youth.cn/",
        "domain": "youth.cn",
    },
    # ===== 热点聚合 =====
    {
        "name": "知乎热点",
        "priority": 8,
        "rss_urls": [],
        "custom_crawl": _zhihu_crawl,
    },
]


PRIORITY_MAP = {s["name"]: s["priority"] for s in SOURCES}

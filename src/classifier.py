from typing import List

from src.config import CATEGORY_KEYWORDS
from src.models import NewsItem


def classify(item: NewsItem) -> str:
    text = item.title + " " + (item.summary or "")
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[cat] += 1

    # 头条一票优先
    if scores.get("头条", 0) > 0:
        return "头条"

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "中国"


def classify_all(items: List[NewsItem]) -> List[NewsItem]:
    for it in items:
        if not it.category:
            it.category = classify(it)
    return items

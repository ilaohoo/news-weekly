from collections import Counter
from math import sqrt
from typing import List

import jieba

from src.config import DEDUP_SIMILARITY_THRESHOLD
from src.models import NewsItem
from src.sources import PRIORITY_MAP as SOURCE_PRIORITY

_STOP = {"的", "了", "在", "是", "和", "与", "及", "等", "为", "对",
         "从", "以", "有", "被", "这", "那", "一个", "我们", "他们"}


def _tokens(text: str) -> List[str]:
    return [w for w in jieba.cut(text) if len(w) > 1 and w not in _STOP]


def _cosine(a: Counter, b: Counter) -> float:
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    na = sqrt(sum(v * v for v in a.values()))
    nb = sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def dedup(items: List[NewsItem]) -> List[NewsItem]:
    ordered = sorted(items, key=lambda x: SOURCE_PRIORITY.get(x.source, 99))
    kept: List[NewsItem] = []
    vecs: List[Counter] = []

    for it in ordered:
        vec = Counter(_tokens(it.title + " " + (it.summary or "")))
        if vec and any(_cosine(vec, v) >= DEDUP_SIMILARITY_THRESHOLD for v in vecs):
            continue
        kept.append(it)
        vecs.append(vec)

    return kept

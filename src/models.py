from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published: Optional[str] = None
    summary: str = ""
    category: str = ""
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())

"""每日采集入口。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.classifier import classify_all
from src.collectors.unified import build_collectors
from src.storage import cleanup_old, init_db, save_items


def main() -> None:
    init_db()
    total = 0
    for collector in build_collectors():
        try:
            items = collector.collect()
            classify_all(items)
            saved = save_items(items)
            total += saved
            print(f"[{collector.name}] 采集 {len(items)} 条 / 新增 {saved} 条")
        except Exception as e:
            print(f"[{collector.name}] 异常: {e}")

    cleanup_old(days=30)
    print(f"\n采集完成，共新增 {total} 条")


if __name__ == "__main__":
    main()

"""每日采集入口（并行版）。"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.classifier import classify_all
from src.collectors.unified import build_collectors
from src.storage import cleanup_old, init_db, save_items


def _collect_one(collector):
    """采集单个源，返回 (源名称, 采集条数, 新增条数, 错误信息)。"""
    try:
        items = collector.collect()
        classify_all(items)
        saved = save_items(items)
        return (collector.name, len(items), saved, None)
    except Exception as e:
        return (collector.name, 0, 0, str(e))


def main() -> None:
    init_db()
    total = 0
    collectors = build_collectors()

    print(f"开始采集 {len(collectors)} 个新闻源（最多 6 个并发）...")

    # 并行执行所有源，最多 6 个并发
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_collect_one, c): c for c in collectors}
        for future in as_completed(futures, timeout=300):
            try:
                name, count, saved, err = future.result(timeout=60)
                total += saved
                if err:
                    print(f"[{name}] 异常: {err}")
                else:
                    print(f"[{name}] 采集 {count} 条 / 新增 {saved} 条")
            except Exception as e:
                print(f"[采集异常] {e}")

    cleanup_old(days=30)
    print(f"\n采集完成，共新增 {total} 条")


if __name__ == "__main__":
    main()

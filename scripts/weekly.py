"""每周六汇总入口。"""
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analyzer import analyze_weekly
from src.classifier import classify_all
from src.config import CATEGORIES, SITE_BASE
from src.dedup import dedup
from src.pusher import push
from src.report import build_summary_markdown, render_report
from src.storage import get_recent_items, init_db


def _detect_pages_base() -> str:
    if SITE_BASE:
        return SITE_BASE.rstrip("/")
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if url.startswith("git@"):
            path = url.split(":", 1)[1]
        else:
            path = "/".join(url.rstrip("/").split("/")[-2:])
        path = path.replace(".git", "")
        user, repo = path.split("/", 1)
        return f"https://{user}.github.io/{repo}"
    except Exception:
        return ""


def main() -> None:
    init_db()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[{today}] 开始每周汇总...")

    items = get_recent_items(days=7)
    print(f"读取原始新闻 {len(items)} 条")

    items = dedup(items)
    print(f"语义去重后 {len(items)} 条")

    classify_all(items)
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it.category].append(it)
    for cat in CATEGORIES:
        print(f"  {cat}: {len(by_cat.get(cat, []))} 条")

    if not items:
        print("本周无新闻，跳过。")
        return

    print("调用 DeepSeek 分析中（预计 3-6 分钟）...")
    analysis = analyze_weekly(by_cat)

    html_path = render_report(analysis, today)
    print(f"HTML 报告生成: {html_path}")

    base = _detect_pages_base()
    if base:
        full_url = f"{base}/{today}.html"
    else:
        full_url = "（请在仓库 docs/ 目录查看完整版）"

    md = build_summary_markdown(analysis, full_url, today)
    push(f"📰 大少年新闻周报 · {today}", md)


if __name__ == "__main__":
    main()

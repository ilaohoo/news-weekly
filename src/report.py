from datetime import datetime
from pathlib import Path

from jinja2 import Template

from src.config import DOCS_DIR

_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>大少年新闻周报 · {{ date }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f0f2f5; color: #1a1a1a; line-height: 1.75;
    padding: 16px; -webkit-font-smoothing: antialiased;
  }
  .container { max-width: 820px; margin: 0 auto; }

  /* ===== 封面 ===== */
  .cover {
    background: linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #ffb347 100%);
    color: #fff; padding: 44px 34px; border-radius: 20px;
    margin-bottom: 26px; box-shadow: 0 12px 32px rgba(255,107,53,0.22);
    position: relative; overflow: hidden;
  }
  .cover::before {
    content: ""; position: absolute; top: -60px; right: -60px;
    width: 200px; height: 200px; border-radius: 50%;
    background: rgba(255,255,255,0.12);
  }
  .cover::after {
    content: ""; position: absolute; bottom: -80px; right: 60px;
    width: 140px; height: 140px; border-radius: 50%;
    background: rgba(255,255,255,0.08);
  }
  .cover-badge {
    display: inline-block; background: rgba(255,255,255,0.22);
    padding: 5px 14px; border-radius: 20px; font-size: 13px;
    margin-bottom: 16px; backdrop-filter: blur(4px);
  }
  .cover h1 { font-size: 32px; margin-bottom: 18px; letter-spacing: 1px; }
  .cover .headline {
    font-size: 19px; line-height: 1.6; font-weight: 500;
    padding: 16px 20px; background: rgba(255,255,255,0.16);
    border-radius: 12px; margin-bottom: 20px; backdrop-filter: blur(4px);
  }
  .cover .keywords { margin-bottom: 22px; }
  .cover .keyword {
    display: inline-block; background: rgba(255,255,255,0.28);
    padding: 4px 12px; border-radius: 14px; font-size: 13px;
    margin: 0 8px 8px 0;
  }
  .cover .points { list-style: none; }
  .cover .points li {
    padding: 8px 0 8px 24px; position: relative; font-size: 15px;
    border-bottom: 1px dashed rgba(255,255,255,0.2);
  }
  .cover .points li:last-child { border-bottom: none; }
  .cover .points li::before {
    content: "▸"; position: absolute; left: 0; opacity: 0.85;
  }

  /* ===== 栏目 ===== */
  .category {
    background: #fff; border-radius: 20px; padding: 34px 32px;
    margin-bottom: 24px; box-shadow: 0 3px 16px rgba(0,0,0,0.05);
  }
  .category-title {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 20px; padding-bottom: 16px;
    border-bottom: 2px solid #f5f5f5;
  }
  .category-title .icon {
    width: 42px; height: 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; background: linear-gradient(135deg, #ff6b35, #f7931e);
    box-shadow: 0 4px 12px rgba(255,107,53,0.25);
  }
  .category-title h2 { font-size: 22px; color: #ff6b35; font-weight: 700; }

  .overview {
    background: linear-gradient(135deg, #fff8f3 0%, #fff3ec 100%);
    padding: 20px 22px; border-radius: 14px; margin-bottom: 26px;
    font-size: 15px; color: #444; line-height: 1.8;
    border-left: 4px solid #ffb347;
  }

  /* ===== 重点新闻 ===== */
  .highlight {
    padding-top: 24px; margin-top: 24px; border-top: 1px dashed #ebeef2;
  }
  .highlight:first-of-type { padding-top: 0; margin-top: 0; border-top: none; }
  .highlight h3 {
    font-size: 18px; margin-bottom: 10px; line-height: 1.5; color: #222;
  }
  .highlight .meta {
    font-size: 13px; color: #999; margin-bottom: 18px;
    display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  }
  .highlight .meta .source-tag {
    background: #f5f5f5; color: #666; padding: 2px 10px;
    border-radius: 10px; font-size: 12px;
  }
  .highlight .meta a { color: #ff6b35; text-decoration: none; font-weight: 500; }
  .highlight .meta a:hover { text-decoration: underline; }

  .dimension {
    margin-bottom: 12px; padding: 14px 18px;
    background: #fafbfc; border-radius: 12px;
    border-left: 4px solid #ddd; transition: background 0.2s;
  }
  .dimension:hover { background: #f5f7fa; }
  .dimension .label {
    font-weight: 600; font-size: 13px; margin-bottom: 6px;
    display: inline-flex; align-items: center; gap: 5px;
  }
  .dimension p { font-size: 14px; color: #333; line-height: 1.8; }
  .dimension.knowledge { border-left-color: #4a90e2; }
  .dimension.knowledge .label { color: #4a90e2; }
  .dimension.history { border-left-color: #8e6e53; }
  .dimension.history .label { color: #8e6e53; }
  .dimension.global { border-left-color: #16a085; }
  .dimension.global .label { color: #16a085; }
  .dimension.thinking { border-left-color: #9b59b6; }
  .dimension.thinking .label { color: #9b59b6; }
  .dimension.subject { border-left-color: #27ae60; }
  .dimension.subject .label { color: #27ae60; }
  .dimension.writing { border-left-color: #e67e22; }
  .dimension.writing .label { color: #e67e22; }

  /* ===== 时事薯条 ===== */
  .fries-grid {
    display: grid; grid-template-columns: 1fr; gap: 12px;
  }
  .fries-card {
    background: #fffdf5; border-radius: 12px; padding: 14px 18px;
    border-left: 4px solid #f5b041;
  }
  .fries-card .fries-title {
    font-size: 15px; font-weight: 600; color: #333; margin-bottom: 6px;
  }
  .fries-card .fries-comment {
    font-size: 13px; color: #666; margin-bottom: 6px;
  }
  .fries-card .fries-knowledge {
    font-size: 12px; color: #d68910;
    background: #fff8e6; padding: 4px 10px; border-radius: 8px;
    display: inline-block;
  }

  /* ===== 副刊 ===== */
  .supplement {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    color: #fff; border-radius: 20px; padding: 36px 32px;
    margin-bottom: 24px; box-shadow: 0 8px 24px rgba(44,62,80,0.2);
  }
  .supplement h2 {
    font-size: 24px; margin-bottom: 10px; display: flex;
    align-items: center; gap: 10px; color: #fff;
  }
  .supplement .topic {
    font-size: 15px; opacity: 0.85; margin-bottom: 26px;
    padding-left: 34px;
  }
  .perspective {
    background: rgba(255,255,255,0.08); border-radius: 14px;
    padding: 20px 22px; margin-bottom: 14px;
    border-left: 3px solid #ffb347;
    backdrop-filter: blur(4px);
  }
  .perspective:last-child { margin-bottom: 0; }
  .perspective .role {
    font-size: 13px; font-weight: 600; color: #ffb347;
    margin-bottom: 8px; letter-spacing: 0.5px;
  }
  .perspective p { font-size: 14px; line-height: 1.85; color: #eaeaea; }

  /* ===== 观点碰撞 ===== */
  .debate {
    background: #fff; border-radius: 20px; padding: 34px 32px;
    margin-bottom: 24px; box-shadow: 0 3px 16px rgba(0,0,0,0.05);
  }
  .debate h2 {
    font-size: 22px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px; color: #c0392b;
  }
  .debate .debate-topic {
    font-size: 16px; color: #555; margin-bottom: 24px;
    padding-left: 34px;
  }
  .debate-sides {
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
    margin-bottom: 20px;
  }
  @media (max-width: 640px) {
    .debate-sides { grid-template-columns: 1fr; }
  }
  .side {
    padding: 18px 20px; border-radius: 14px; font-size: 14px; line-height: 1.8;
  }
  .side-a {
    background: #eaf4fd; border-left: 4px solid #3498db; color: #2c3e50;
  }
  .side-b {
    background: #fdeaea; border-left: 4px solid #e74c3c; color: #2c3e50;
  }
  .side .side-label {
    font-weight: 700; font-size: 13px; margin-bottom: 8px; display: block;
  }
  .side-a .side-label { color: #3498db; }
  .side-b .side-label { color: #e74c3c; }
  .stance {
    background: #f8f9fa; padding: 18px 20px; border-radius: 14px;
    border-left: 4px solid #95a5a6; font-size: 14px; line-height: 1.8;
    color: #444;
  }
  .stance .stance-label {
    font-weight: 700; font-size: 13px; color: #7f8c8d;
    margin-bottom: 8px; display: block;
  }

  /* ===== 思考题 ===== */
  .discussion {
    background: linear-gradient(135deg, #fffbea 0%, #fff5d6 100%);
    border-radius: 20px; padding: 34px 32px; margin-bottom: 24px;
    box-shadow: 0 3px 16px rgba(0,0,0,0.05);
    border: 1px solid #ffe4a8;
  }
  .discussion h2 {
    font-size: 22px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 10px; color: #d68910;
  }
  .discussion .question {
    font-size: 17px; font-weight: 600; color: #333;
    padding: 18px 20px; background: #fff; border-radius: 12px;
    margin-bottom: 20px; line-height: 1.7;
    border-left: 4px solid #f5b041;
  }
  .hints-title {
    font-size: 14px; font-weight: 600; color: #d68910;
    margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
  }
  .hints ul { list-style: none; margin-bottom: 20px; }
  .hints li {
    padding: 8px 0 8px 22px; position: relative;
    font-size: 14px; color: #555;
  }
  .hints li::before {
    content: "○"; position: absolute; left: 0; color: #f5b041;
    font-weight: bold;
  }
  .writing-tips {
    background: #fff; border-radius: 12px; padding: 16px 20px;
  }
  .writing-tips p { font-size: 14px; color: #555; line-height: 1.8; }

  /* ===== 页脚 ===== */
  footer {
    text-align: center; color: #999; font-size: 13px;
    padding: 32px 0 12px; line-height: 1.8;
  }
  footer .brand { color: #ff6b35; font-weight: 600; }
</style>
</head>
<body>
<div class="container">

  <!-- ============ 封面导读 ============ -->
  {% if cover %}
  <header class="cover">
    <div class="cover-badge">📅 {{ date }} · 每周六更新</div>
    <h1>📰 大少年新闻周报</h1>
    {% if cover.headline %}<div class="headline">{{ cover.headline }}</div>{% endif %}
    {% if cover.keywords %}
    <div class="keywords">
      {% for kw in cover.keywords %}<span class="keyword"># {{ kw }}</span>{% endfor %}
    </div>
    {% endif %}
    {% if cover.points %}
    <ul class="points">
      {% for p in cover.points %}<li>{{ p }}</li>{% endfor %}
    </ul>
    {% endif %}
  </header>
  {% endif %}

  <!-- ============ 各栏目 ============ -->
  {% for cat in categories %}
  <section class="category">
    <div class="category-title">
      <div class="icon">{{ cat.icon | default('📌') }}</div>
      <h2>{{ cat.name }}</h2>
    </div>

    {% if cat.overview %}<div class="overview">{{ cat.overview }}</div>{% endif %}

    {# ---------- 时事薯条：特殊布局 ---------- #}
    {% if cat.name == "时事薯条" and cat.fries %}
    <div class="fries-grid">
      {% for f in cat.fries %}
      <div class="fries-card">
        <div class="fries-title">{{ f.title }}</div>
        {% if f.comment %}<div class="fries-comment">💬 {{ f.comment }}</div>{% endif %}
        {% if f.knowledge %}<span class="fries-knowledge">📚 {{ f.knowledge }}</span>{% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {# ---------- 普通重点新闻 ---------- #}
    {% for h in cat.highlights %}
    <div class="highlight">
      <h3>{{ h.title }}</h3>
      <div class="meta">
        <span class="source-tag">{{ h.source }}</span>
        {% if h.url %}<a href="{{ h.url }}" target="_blank">阅读原文 →</a>{% endif %}
      </div>
      {% if h.knowledge %}<div class="dimension knowledge">
        <span class="label">📚 知识拓展</span><p>{{ h.knowledge }}</p></div>{% endif %}
      {% if h.history %}<div class="dimension history">
        <span class="label">📜 历史纵深</span><p>{{ h.history }}</p></div>{% endif %}
      {% if h.global %}<div class="dimension global">
        <span class="label">🌐 全球对比</span><p>{{ h.global }}</p></div>{% endif %}
      {% if h.thinking %}<div class="dimension thinking">
        <span class="label">💭 思辨启发</span><p>{{ h.thinking }}</p></div>{% endif %}
      {% if h.subject %}<div class="dimension subject">
        <span class="label">🎓 学科关联</span><p>{{ h.subject }}</p></div>{% endif %}
      {% if h.writing %}<div class="dimension writing">
        <span class="label">✍️ 写作素材</span><p>{{ h.writing }}</p></div>{% endif %}
    </div>
    {% endfor %}
  </section>
  {% endfor %}

  <!-- ============ 副刊 ============ -->
  {% if supplement and supplement.perspectives %}
  <section class="supplement">
    <h2>🎭 副刊</h2>
    {% if supplement.topic %}<div class="topic">本期话题：{{ supplement.topic }}</div>{% endif %}
    {% for p in supplement.perspectives %}
    <div class="perspective">
      <div class="role">{{ p.role }}</div>
      <p>{{ p.view }}</p>
    </div>
    {% endfor %}
  </section>
  {% endif %}

  <!-- ============ 观点碰撞 ============ -->
  {% if debate and debate.topic %}
  <section class="debate">
    <h2>⚔️ 观点碰撞</h2>
    <div class="debate-topic">本期话题：{{ debate.topic }}</div>
    <div class="debate-sides">
      {% if debate.side_a %}
      <div class="side side-a">
        <span class="side-label">观点 A</span>
        {{ debate.side_a }}
      </div>
      {% endif %}
      {% if debate.side_b %}
      <div class="side side-b">
        <span class="side-label">观点 B</span>
        {{ debate.side_b }}
      </div>
      {% endif %}
    </div>
    {% if debate.stance %}
    <div class="stance">
      <span class="stance-label">🤔 AI 的立场</span>
      {{ debate.stance }}
    </div>
    {% endif %}
  </section>
  {% endif %}

  <!-- ============ 本周思考题 ============ -->
  {% if discussion and discussion.question %}
  <section class="discussion">
    <h2>💡 本周思考题</h2>
    <div class="question">{{ discussion.question }}</div>
    {% if discussion.hints %}
    <div class="hints">
      <div class="hints-title">🧭 思路提示</div>
      <ul>{% for h in discussion.hints %}<li>{{ h }}</li>{% endfor %}</ul>
    </div>
    {% endif %}
    {% if discussion.writing_tips %}
    <div class="writing-tips">
      <div class="hints-title">✍️ 写作建议</div>
      <p>{{ discussion.writing_tips }}</p>
    </div>
    {% endif %}
  </section>
  {% endif %}

  <footer>
    <div><span class="brand">大少年新闻周报</span> · 每周六更新</div>
    <div>由 DeepSeek 生成分析 · 数据来自新华网、人民网等公开新闻源</div>
    <div>本报告仅供学习参考</div>
  </footer>
</div>
</body>
</html>
"""


_CATEGORY_ICONS = {
    "头条": "🔥",
    "中国": "🇨🇳",
    "世界": "🌍",
    "科学": "🔬",
    "文化": "🎨",
    "教育": "📖",
    "体育": "⚽",
    "经济": "💰",
    "人物": "🌟",
    "时事薯条": "🍟",
}


def render_report(analysis: dict, date_str: str | None = None) -> Path:
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")

    for cat in analysis.get("categories", []):
        if not cat.get("icon"):
            cat["icon"] = _CATEGORY_ICONS.get(cat.get("name", ""), "📌")

    html = Template(_TEMPLATE).render(
        date=date_str,
        cover=analysis.get("cover", {}),
        categories=analysis.get("categories", []),
        supplement=analysis.get("supplement", {}),
        debate=analysis.get("debate", {}),
        discussion=analysis.get("discussion", {}),
    )

    out = DOCS_DIR / f"{date_str}.html"
    out.write_text(html, encoding="utf-8")
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    return out


def build_summary_markdown(analysis: dict, full_url: str, date_str: str) -> str:
    """生成推送到微信的摘要（控制在 1500 字以内）。"""
    lines = [f"## 📰 大少年新闻周报 · {date_str}\n"]

    # 封面导读
    cover = analysis.get("cover", {})
    if cover.get("headline"):
        lines.append(f"> **{cover['headline']}**\n")
    if cover.get("points"):
        for p in cover["points"][:4]:
            lines.append(f"- {p}")
        lines.append("")

    # 各栏目：只列标题
    for cat in analysis.get("categories", []):
        name = cat.get("name", "")
        if not name or name == "时事薯条":
            continue
        highlights = cat.get("highlights", [])
        if not highlights:
            continue
        icon = cat.get("icon", "📌")
        lines.append(f"### {icon} {name}")
        for h in highlights[:3]:
            lines.append(f"- {h.get('title', '')}")
        lines.append("")

    # 薯条：列前 5 条
    for cat in analysis.get("categories", []):
        if cat.get("name") != "时事薯条":
            continue
        fries = cat.get("fries", [])
        if fries:
            lines.append(f"### 🍟 时事薯条")
            for f in fries[:5]:
                lines.append(f"- {f.get('title', '')}")
            lines.append("")

    # 副刊
    supp = analysis.get("supplement", {})
    if supp.get("topic") and supp.get("perspectives"):
        lines.append(f"### 🎭 副刊 · {supp['topic']}")
        first = supp["perspectives"][0]
        view = first.get("view", "")
        excerpt = view[:100] + ("..." if len(view) > 100 else "")
        lines.append(f"> {first.get('role', '')}：{excerpt}")
        lines.append("")

    # 观点碰撞
    debate = analysis.get("debate", {})
    if debate.get("topic"):
        lines.append(f"### ⚔️ 观点碰撞 · {debate['topic']}")
        lines.append("")

    # 思考题
    disc = analysis.get("discussion", {})
    if disc.get("question"):
        lines.append(f"### 💡 本周思考题")
        lines.append(f"{disc['question']}\n")

    lines.append(f"👉 [阅读完整版周报]({full_url})")
    return "\n".join(lines)

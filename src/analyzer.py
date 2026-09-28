import json
import re
from typing import Dict, List

import requests

from src.config import (
    CORE_CATEGORIES, DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL,
    EXTENDED_CATEGORIES, MAX_ITEMS_PER_CATEGORY_FOR_AI,
)
from src.models import NewsItem
from src.sources import PRIORITY_MAP

SYSTEM_PROMPT = """你是一位面向中国中学生（初中/高中）的新闻编辑，风格参考《大少年》报纸。

你的风格要求：
- 语言平实、有温度，不说官腔，不说教
- 注重背景解释，帮学生真正看懂新闻
- 引导独立思考，不灌输结论
- 学科关联必须精确到具体教材版本 + 年级 + 单元/章节，例如"人教版八年级上册第四单元·维护国家利益"，不能只说"地理相关"
- 提供可直接使用的写作素材

严格要求：只输出合法 JSON，不要添加任何多余文字或 markdown 代码块标记。"""


# ============================================================
# 调用一：封面 + 栏目总览 + 薯条 + 副刊 + 观点碰撞 + 思考题
# ============================================================
_PROMPT_OVERVIEW = """以下是一周内采集到的新闻，已按栏目粗分类：

{content}

请你完成以下任务，并严格按 JSON 输出。

## 任务一：封面导读
- headline：一句话概括本周最值得中学生关注的核心看点（30 字以内）
- points：3-5 条本周看点，每条不超过 30 字
- keywords：3-5 个本周关键词（短语）

## 任务二：栏目总览
对每个有新闻的栏目，写一段 150-250 字的【栏目总览】。不要挑重点新闻，只写总览。

## 任务三：时事薯条
将时事薯条栏目改为"一句话点评 + 一个知识点"格式，输出 6-8 条：
- title：短讯标题（15字内）
- comment：一句点评（30字内）
- knowledge：一个知识点（30字内，标注学科）

## 任务四：副刊
提炼一个值得深挖的话题，让三位不同领域专家从各自视角解读：
- topic：本期副刊主题（8-15 字）
- perspectives：3 个对象，每个有 role（专家角色）和 view（200-300字）

## 任务五：观点碰撞
挑一件有讨论空间的新闻：
- topic：争议话题（15字内）
- side_a：观点 A（150-250字）
- side_b：观点 B（150-250字）
- stance：AI 的立场（150-250字），指出双方成立的前提

## 任务六：本周思考题
- question：一道开放性问题
- hints：2-3 条思路提示
- writing_tips：100-150 字写作建议

## 输出 JSON 格式

{{
  "cover": {{"headline": "...", "points": ["...", "..."], "keywords": ["...", "..."]}},
  "categories": [
    {{"name": "栏目名", "overview": "..."}}
  ],
  "fries": [
    {{"title": "...", "comment": "...", "knowledge": "...（地理）"}}
  ],
  "supplement": {{
    "topic": "...",
    "perspectives": [
      {{"role": "...", "view": "..."}},
      {{"role": "...", "view": "..."}},
      {{"role": "...", "view": "..."}}
    ]
  }},
  "debate": {{
    "topic": "...",
    "side_a": "...",
    "side_b": "...",
    "stance": "..."
  }},
  "discussion": {{
    "question": "...",
    "hints": ["...", "..."],
    "writing_tips": "..."
  }}
}}"""


# ============================================================
# 调用二：核心栏目重点新闻（六维解读）
# ============================================================
_PROMPT_CORE = """以下是一周内采集到的核心栏目新闻：

{content}

请为每个栏目挑选最有价值的 2 条重点新闻，每条按六个维度解读：

- knowledge 知识拓展（100-200字）：课本没讲到但能帮你理解新闻的背景
- history 历史纵深（80-150字）：这件事在历史上的来龙去脉
- global 全球对比（80-150字）：其他国家怎么做，中国的位置在哪
- thinking 思辨启发（100-200字）：不同角度的思考方向
- subject 学科关联（80-150字）：写明教材版本+年级+单元/章节
- writing 写作素材（100-200字）：可作为什么主题的作文素材，给一个开头示例

严格按 JSON 输出：

{{
  "categories": [
    {{
      "name": "栏目名",
      "highlights": [
        {{
          "title": "...",
          "source": "...",
          "url": "...",
          "knowledge": "...",
          "history": "...",
          "global": "...",
          "thinking": "...",
          "subject": "...",
          "writing": "..."
        }}
      ]
    }}
  ]
}}"""


# ============================================================
# 调用三：扩展栏目重点新闻（四维解读）
# ============================================================
_PROMPT_EXT = """以下是一周内采集到的扩展栏目新闻：

{content}

请为每个栏目挑选最有价值的 2 条重点新闻，每条按四个维度解读：

- knowledge 知识拓展（100-150字）
- thinking 思辨启发（100-150字）
- subject 学科关联（80-120字）：写明教材版本+年级+单元/章节
- writing 写作素材（100-150字）：给一个开头示例

严格按 JSON 输出：

{{
  "categories": [
    {{
      "name": "栏目名",
      "highlights": [
        {{
          "title": "...",
          "source": "...",
          "url": "...",
          "knowledge": "...",
          "thinking": "...",
          "subject": "...",
          "writing": "..."
        }}
      ]
    }}
  ]
}}"""


def _call_deepseek(prompt: str) -> dict:
    """通用的 DeepSeek 调用，返回解析后的 JSON。"""
    resp = requests.post(
        DEEPSEEK_API_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
        },
        timeout=900,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()

    # 第一次尝试：strict=False 允许字符串内出现控制字符（如未转义的换行符）
    try:
        return json.loads(content, strict=False)
    except json.JSONDecodeError as e:
        print(f"[JSON 解析失败，尝试清理控制字符] {e}")

    # 兜底：逐字符清理字符串内的裸控制字符，保留 \n(0x0a) 和 \t(0x09)
    cleaned = re.sub(
        r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',
        '',
        content,
    )
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        print(f"[JSON 解析仍然失败] {e}")
        print(f"[原始返回前 800 字] {content[:800]}")
        raise


def analyze_weekly(by_cat: Dict[str, List[NewsItem]]) -> dict:
    """分三次调用 DeepSeek，合并结果。"""
    full_content = _build_input(by_cat, max_per_cat=MAX_ITEMS_PER_CATEGORY_FOR_AI)

    # ---- 调用一：整体结构 ----
    print("[1/3] 生成封面、栏目总览、副刊、观点碰撞、思考题...")
    result = _call_deepseek(_PROMPT_OVERVIEW.format(content=full_content))

    # ---- 调用二：核心栏目重点新闻 ----
    core_content = _build_input(
        {k: v for k, v in by_cat.items() if k in CORE_CATEGORIES},
        max_per_cat=8,
    )
    core_result = {"categories": []}
    if core_content.strip():
        print("[2/3] 生成核心栏目重点新闻（六维解读）...")
        core_result = _call_deepseek(_PROMPT_CORE.format(content=core_content))

    # ---- 调用三：扩展栏目重点新闻 ----
    ext_content = _build_input(
        {k: v for k, v in by_cat.items() if k in EXTENDED_CATEGORIES},
        max_per_cat=8,
    )
    ext_result = {"categories": []}
    if ext_content.strip():
        print("[3/3] 生成扩展栏目重点新闻（四维解读）...")
        ext_result = _call_deepseek(_PROMPT_EXT.format(content=ext_content))

    # ---- 合并：把重点新闻挂到对应的栏目上 ----
    highlights_map = {}
    for item in core_result.get("categories", []) + ext_result.get("categories", []):
        highlights_map[item.get("name", "")] = item.get("highlights", [])

    for cat in result.get("categories", []):
        cat["highlights"] = highlights_map.get(cat.get("name", ""), [])

    # ---- 薯条栏目挂上 fries ----
    if result.get("fries"):
        for cat in result["categories"]:
            if cat.get("name") == "时事薯条":
                cat["fries"] = result["fries"]
                break
        else:
            result["categories"].append({
                "name": "时事薯条",
                "overview": "",
                "highlights": [],
                "fries": result["fries"],
            })

    return result


def _build_input(by_cat: Dict[str, List[NewsItem]], max_per_cat: int = 12) -> str:
    from src.config import CATEGORIES
    lines = []
    for cat in CATEGORIES:
        items = sorted(
            by_cat.get(cat, []),
            key=lambda x: PRIORITY_MAP.get(x.source, 99),
        )[:max_per_cat]
        if not items:
            continue
        lines.append(f"### 栏目：{cat}（共 {len(items)} 条）")
        for i, it in enumerate(items, 1):
            s = (it.summary or "")[:100]
            lines.append(f"{i}. [{it.source}] {it.title}｜{s}｜{it.url}")
        lines.append("")
    return "\n".join(lines)

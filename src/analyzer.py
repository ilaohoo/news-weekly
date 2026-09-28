import json
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


USER_PROMPT_TEMPLATE = """以下是一周内采集到的新闻，已按栏目粗分类：

{content}

请你完成以下任务，并严格按 JSON 输出。

## 任务一：封面导读
- headline：一句话概括本周最值得中学生关注的核心看点（30 字以内）
- points：3-5 条本周看点，每条不超过 30 字
- keywords：3-5 个本周关键词（短语）

## 任务二：栏目总览 + 重点新闻

对每个有新闻的栏目：
- 剔除重复或无关新闻，选出最有价值的 2-3 条重点新闻
- 写一段 150-250 字的【栏目总览】
- 为每条重点新闻写解读：
  - 核心栏目（头条/中国/世界/科学/文化）：写六维解读
    - knowledge 知识拓展（100-200字）
    - history 历史纵深（80-150字）：这件事在历史上的来龙去脉
    - global 全球对比（80-150字）：其他国家怎么做的，中国的位置在哪
    - thinking 思辨启发（100-200字）
    - subject 学科关联（80-150字）：写明教材版本+年级+单元/章节
    - writing 写作素材（100-200字）：给一个具体的开头示例
  - 扩展栏目（教育/体育/经济/人物）：写四维解读
    - knowledge 知识拓展
    - thinking 思辨启发
    - subject 学科关联
    - writing 写作素材

## 任务三：时事薯条改造
时事薯条栏目改为“一句话点评 + 一个知识点”格式：
- 每条包含：短讯标题 + 一句点评（30字内）+ 一个知识点（30字内，标注学科）

## 任务四：副刊
从本周新闻中提炼一个值得深挖的话题，让三位不同领域专家从各自视角解读：
- topic：本期副刊主题（8-15 字）
- perspectives：数组，包含 3 个对象，每个有 role（专家角色）和 view（200-300字解读）

## 任务五：观点碰撞
挑一件有讨论空间的新闻，呈现两种不同立场：
- topic：争议话题（15字内）
- side_a：观点 A（150-250字）
- side_b：观点 B（150-250字）
- stance：AI 的立场（150-250字），不站队但指出双方各自成立的前提

## 任务六：本周思考题
- question：一道开放性问题
- hints：2-3 条思路提示
- writing_tips：100-150 字写作建议

## 输出 JSON 格式

{{
  "cover": {{
    "headline": "...",
    "points": ["...", "..."],
    "keywords": ["...", "..."]
  }},
  "categories": [
    {{
      "name": "栏目名",
      "overview": "...",
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
      ],
      "fries": [
        {{"title": "...", "comment": "...", "knowledge": "...（地理/物理等）"}}
      ]
    }}
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


def analyze_weekly(by_cat: Dict[str, List[NewsItem]]) -> dict:
    content = _build_input(by_cat)
    user_prompt = USER_PROMPT_TEMPLATE.format(content=content)

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
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        },
        timeout=900,
    )
    resp.raise_for_status()
    content_str = resp.json()["choices"][0]["message"]["content"].strip()

    if content_str.startswith("```"):
        content_str = content_str.strip("`")
        if content_str.startswith("json"):
            content_str = content_str[4:].strip()

    return json.loads(content_str)


def _build_input(by_cat: Dict[str, List[NewsItem]]) -> str:
    from src.config import CATEGORIES
    lines = []
    for cat in CATEGORIES:
        items = sorted(
            by_cat.get(cat, []),
            key=lambda x: PRIORITY_MAP.get(x.source, 99),
        )[:MAX_ITEMS_PER_CATEGORY_FOR_AI]
        if not items:
            continue
        lines.append(f"### 栏目：{cat}（共 {len(items)} 条）")
        for i, it in enumerate(items, 1):
            s = (it.summary or "")[:100]
            lines.append(f"{i}. [{it.source}] {it.title}｜{s}｜{it.url}")
        lines.append("")
    return "\n".join(lines)

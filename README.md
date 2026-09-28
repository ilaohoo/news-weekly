# 大少年新闻周报

面向初高中生的新闻资讯聚合与 AI 深度解读工具。

## 功能

- 每日自动采集：新华网、人民网、新浪、搜狐、网易、凤凰网、知乎热点、参考消息、未来网、中国教育新闻网、华奥星空、中国科普网、中国青年网
- 每周六自动生成：DeepSeek 按《大少年》栏目结构撰写总览和深度解读
- 微信推送：通过 PushPlus 推送摘要，附带 GitHub Pages 完整版链接

## 栏目结构

封面导读 / 头条 / 中国 / 世界 / 科学 / 文化 / 教育 / 体育 / 经济 / 人物 / 时事薯条 / 副刊 / 观点碰撞 / 本周思考题

每条重点新闻包含四到六维解读。

## 本地运行

```bash
pip install -r requirements.txt

# 采集
python scripts/collect.py

# 汇总（需要环境变量）
export DEEPSEEK_API_KEY=sk-xxx
export PUSHPLUS_TOKEN=your_token
export SITE_BASE=https://yourname.github.io/news-weekly
python scripts/weekly.py

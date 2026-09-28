import requests

from src.config import PUSHPLUS_TOKEN


def push(title: str, content: str) -> bool:
    if not PUSHPLUS_TOKEN:
        print("[PushPlus] 未配置 token，跳过推送")
        return False

    try:
        resp = requests.post(
            "http://www.pushplus.plus/send",
            json={
                "token": PUSHPLUS_TOKEN,
                "title": title[:100],
                "content": content,
                "template": "markdown",
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("code") == 200:
            print("[PushPlus] 推送成功")
            return True
        print(f"[PushPlus] 推送失败: {data}")
        return False
    except Exception as e:
        print(f"[PushPlus] 请求异常: {e}")
        return False

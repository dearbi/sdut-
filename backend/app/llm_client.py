import os
import json
import httpx
from typing import Tuple

DEFAULT_API_URL = os.getenv("SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
MODEL = os.getenv("SILICONFLOW_MODEL", "qwen-turbo")
API_KEY = os.getenv("SILICONFLOW_API_KEY")

try:
    from ._local_secrets import SILICONFLOW_API_KEY as _LOCAL_API_KEY
except Exception:
    _LOCAL_API_KEY = None
API_KEY = API_KEY or _LOCAL_API_KEY

SYSTEM_PROMPT = (
    "你是一位医学文档编辑专家。请对报告进行专业化优化：\n"
    "- 统一格式与排版（标题/小节/表格）\n"
    "- 修正语法与措辞（保持中文医学术语规范）\n"
    "- 增强逻辑性与条理（风险→依据→建议）\n"
    "- 严禁泄露任何个人身份信息，若出现姓名/联系方式等，请使用[REDACTED]替代\n"
    "- 保留关键数据的准确性，不随意修改数值\n"
)

def _redact(html: str) -> str:
    repl = html
    for token in ["受检人：", "联系方式：", "电话：", "邮箱：", "姓名："]:
        repl = repl.replace(token, f"{token}[REDACTED] ")
    return repl

def optimize_report(content: str) -> Tuple[bool, str]:
    if not API_KEY:
        return False, content
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _redact(content)},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    last_error = None
    for attempt in range(3):
        try:
            with httpx.Client(http2=True, timeout=httpx.Timeout(5.0)) as client:
                resp = client.post(DEFAULT_API_URL, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = (
                        data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                    )
                    if text:
                        return True, text
                last_error = f"status={resp.status_code} body={resp.text[:200]}"
        except Exception as e:
            last_error = str(e)
    return False, content
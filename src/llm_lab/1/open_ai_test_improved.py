"""Improved version of open_ai_test.py with bug fixes, type hints, and error handling."""

import os
from typing import Any

from openai import OpenAI

# ── 配置（可从环境变量覆盖）─────────────────────────────
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "lmstudio")
MODEL_DEFAULT_NAME = os.getenv(
    "MODEL_NAME", "lmstudio-community/Qwen3.6-no-thinking"
)

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=API_KEY)

# ── 会话历史 ───────────────────────────────────────────
history_talk: list[dict[str, str]] = [
    {"role": "user", "content": "你好，我是小夏，请记住我"}
]


def print_result_info(response: Any) -> None:
    """打印响应内容（仅对有 output_text 的响应有效）。"""
    if not hasattr(response, "output_text") or response.output_text is None:
        return

    print("=== AI 回复 ===")
    print(response.output_text)
    if hasattr(response, "usage"):
        print(f"input_tokens: {response.usage.input_tokens}")
        print(f"output_tokens: {response.usage.output_tokens}")
        print(f"total_tokens: {response.usage.total_tokens}")


# ── 辅助：发送消息并追加到历史 ──────────────────────────
def send_message(content: str) -> Any:
    """向模型发送消息，自动管理对话历史。"""
    history_talk.append({"role": "user", "content": content})

    response = client.responses.create(
        model=MODEL_DEFAULT_NAME,
        input=history_talk,
    )

    # 记录 AI 回复到历史（用于后续轮次）
    if hasattr(response, "output_text") and response.output_text:
        history_talk.append({"role": "assistant", "content": response.output_text})

    return response


# ── 主流程 ────────────────────────────────────────────
def main() -> None:
    # 1. 初始化对话
    try:
        print(">> 第1轮：初始化")
        send_message("你好，我是小夏，请记住我")
    except Exception as e:
        print(f"API 调用失败: {e}")
        return

    # 2. 多轮记忆测试
    try:
        print("\n>> 第2轮：你是谁？")
        send_message("我是谁？")
    except Exception as e:
        print(f"API 调用失败: {e}")
        return

    # 3. 后台异步任务：生成长篇内容
    print("\n>> 第3轮（后台）：写科幻小说...")
    history_talk.append({"role": "user", "content": "写一篇1000字的科幻小说，以我为主角"})

    try:
        response = client.responses.create(
            model=MODEL_DEFAULT_NAME,
            input=history_talk,
            background=True,
        )
        print(f"status: {response.status}, id: {getattr(response, 'id', None)}")

        poll_interval = 3  # 轮询间隔（秒）
        while response.status in {"queued", "in_progress"}:
            print(f"当前状态：{response.status}，等待 {poll_interval}s...")
            from time import sleep
            sleep(poll_interval)
            response = client.responses.retrieve(response.id)

        if response.status == "completed":
            print("\n=== 后台任务完成 ===")
            print(getattr(response, "output_text", "(无输出)") or "(空输出)")
        else:
            print(f"\n⚠️ 任务状态: {response.status}")

    except Exception as e:
        print(f"后台任务失败: {e}")


if __name__ == "__main__":
    main()

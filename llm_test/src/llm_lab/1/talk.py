import httpx
import asyncio
from pydantic import BaseModel, Field


# ==================== 配置常量 ====================
DEFAULT_LLM_URL = "http://localhost:1234/api/v1/chat"
DEFAULT_MODEL_NAME = "lmstudio-community/Qwen3.6-no-thinking"

# 异步输入：避免在 async 上下文中阻塞事件循环
async def ainput(prompt: str = "") -> str:
    """非阻塞式异步输入"""
    return await asyncio.to_thread(input, prompt)


class LMTalk(BaseModel):
    llm_url: str = Field(default=DEFAULT_LLM_URL, description="LLM API 地址")
    user_input: str = Field(default="", description="用户输入的内容")
    response_msg: str = Field(default="", description="模型的回复内容")

    # HTTP 客户端复用：在类级别创建一次性客户端，避免每次请求都新建连接
    _client: httpx.AsyncClient | None = None

    class Config:
        arbitrary_types_allowed = True  # 允许 httpx.AsyncClient 类型

    @property
    def client(self) -> httpx.AsyncClient:
        """懒加载 HTTP 客户端，复用连接"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Content-Type": "application/json"},
                timeout=60.0,  # 添加超时设置，避免请求无限挂起
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def send_msg(self) -> dict:
        """发送请求并解析响应，包含异常处理"""
        data = {
            "model": DEFAULT_MODEL_NAME,
            "system_prompt": "",
            "input": self.user_input,
        }
        try:
            response = await self.client.post(self.llm_url, json=data)
            response.raise_for_status()  # HTTP 错误状态码抛出异常
            result = response.json()

            # 健壮地解析响应结构
            output = result.get("output", [])
            if output and isinstance(output, list) and len(output) > 0:
                content = output[0].get("content", "")
                self.response_msg = content
            else:
                # fallback：直接使用整个响应字符串
                self.response_msg = str(result)

            return result

        except httpx.HTTPStatusError as e:
            self.response_msg = f"HTTP 错误: {e.response.status_code} - {e.response.text}"
            raise
        except Exception as e:
            self.response_msg = f"请求失败: {type(e).__name__}: {e}"
            raise

    async def talk(self, hello_msg: str = "你想问些什么？"):
        """迭代式对话循环（替代递归，避免 Python 最大递归深度限制）"""
        while True:
            # 使用异步输入，不阻塞事件循环
            user_input = await ainput(hello_msg)

            # 退出条件检查
            if not user_input.strip() or user_input == "退出":
                print("离开对话")
                break

            self.user_input = user_input

            try:
                await self.send_msg()
                print(f"\n回复: {self.response_msg}\n")
            except Exception as e:
                print(f"\n发送失败: {e}\n")
                continue  # 出错时不结束对话，继续下一轮


async def main():
    """异步入口：管理资源生命周期"""
    talk = LMTalk()
    try:
        await talk.talk()
    finally:
        await talk.close()  # 确保 HTTP 客户端被正确关闭


if __name__ == "__main__":
    asyncio.run(main())


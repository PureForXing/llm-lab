from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lmStudio"
)

MODEL_NAME = "lmstudio-community/Qwen3.6-no-thinking"

try:
    print(f"正在测试模型: {MODEL_NAME}")
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "你好，请简单介绍一下自己"}],
        max_tokens=100
    )
    print("响应内容:", response.choices[0].message.content)
except Exception as e:
    print(f"错误信息: {e}")

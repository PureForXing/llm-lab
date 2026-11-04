from pydantic import BaseModel,Field
from openai import OpenAI
from time import sleep

client = OpenAI(
    base_url= "http://127.0.0.1:1234/v1",
    api_key= "lmStudio"
)
MODEL_DEFAULT_NAME = "lmstudio-community/Qwen3.6-no-thinking"

histoy_talk = [{"role":"user","content":"你好，我是小夏，请记住我"}]



def print_result_info(response:any):
    print(response.output_text)
    print("input_tokens:", response.usage.input_tokens)
    print("output_tokens:", response.usage.output_tokens)
    print("total_tokens:", response.usage.total_tokens)

def main():
    response = client.responses.create(
        model=MODEL_DEFAULT_NAME,
        input= histoy_talk
    )
    print_result_info(response)
    histoy_talk.append({"role":"assistant","content":response.output_text})
    print("我是谁？")
    histoy_talk.append({"role":"user","content":"我是谁？"})
    response = client.responses.create(
        model=MODEL_DEFAULT_NAME,
        input= histoy_talk
    )
    print_result_info(response)
    histoy_talk.append({"role":"assistant","content":response.output_text})
    histoy_talk.append({"role":"user","content":"写一篇1000字的科幻小说，以我为主角"})
    response = client.responses.create(
        model=MODEL_DEFAULT_NAME,
        input= histoy_talk,
        background=True
    )
    print("status:", response.status, "id:", getattr(response, "id", None))
    while response.status in {"queued","in_progress"}:
        print(f"当前状态：{response.status}")
        sleep(2)
        response = client.responses.retrieve(response.id)
    print("思考结束")
    print(f"{response.status},-{response.output_text}")
    
    

if __name__ == "__main__":
    main()
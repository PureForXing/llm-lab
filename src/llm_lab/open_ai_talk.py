from pydantic import BaseModel,Field
from openai import OpenAI
from time import sleep

MODEL_DEFAULT_NAME = "lmstudio-community/Qwen3.6-no-thinking"
MODEL_DEFAULT_SYSTEM_PROMPT = """
你是一位专业的心理咨询师，需要根据用户的输入和历史对话记录，
来为用户提供心理帮助，语气要亲切委婉，不要质疑指责用户，或者纠正错误。
你可以尝试了解用户的信息，比如年龄，性别，行业等信息。
然后通过开导引导的方式来沟通。鼓励用户积极面对遇到的困难。
"""
INPUT_PRICE = 2.0   # 元 / 百万 token，可改
OUTPUT_PRICE = 8.0


client = OpenAI(
    base_url= "http://127.0.0.1:1234/v1",
    api_key= "lmStudio"
)

class UserTalk(BaseModel):
    talk_msg:list = Field(default=[{"role": "system", "content": MODEL_DEFAULT_SYSTEM_PROMPT}],description="沟通记录")

def format_user_msg(talk:UserTalk,msg:str):
    talk.talk_msg.append({"role": "user", "content": msg})
    
def format_assistant_msg(talk:UserTalk,msg:str):
    talk.talk_msg.append({"role": "assistant", "content": msg})

def llm_talk(talk:UserTalk):
    sendMsg = get_user_input(talk)
    if not sendMsg:
        print("那我们下次再聊~\n")   
        return
    for i in range(3):
        try:
            completion = client.chat.completions.create(model=MODEL_DEFAULT_NAME,messages=talk.talk_msg)
            print_result_info(completion)
            format_assistant_msg(talk,completion.choices[0].message.content)
            break
        except Exception as e:
            print(f"失败：{e},正在重试第{i}次")
            sleep(2*(i+1))
            if i==2:
                print("LLM服务异常")
            
    llm_talk(talk)

def print_result_info(response:any):
    print(response.choices[0].message.content)
    print(f"input_tokens:{response.usage.prompt_tokens}, output_tokens:{response.usage.completion_tokens},total_tokens:{response.usage.total_tokens}")
    cost = (
        response.usage.prompt_tokens / 1_000_000 * INPUT_PRICE
        + response.usage.completion_tokens / 1_000_000 * OUTPUT_PRICE
    )
    print(f"估算费用: ¥{cost:.6f}")

# 根据用户输入
def get_user_input(talk:UserTalk) -> bool:
    i = 0;
    user_msg = "";
    while i<3:
        i=i+1
        user_msg = input("")
        if user_msg == "":
            print("你有什么想说的都可以告诉我~\n")
            continue
        break
    if user_msg =="" or user_msg.strip() in ["退出","结束","结束聊天","关闭","88","再见"]:
        return False

    if user_msg =="修改提示词":
        input_prompt = input("请输入新的系统提示词\n")
        if input_prompt != "":
            talk.talk_msg = [{"role": "system", "content": input_prompt}]
            print("你好，请问有什么可以帮助你的？")
            get_user_input(talk)
    format_user_msg(talk,user_msg)    
    return True
        
def talk_start():
    print("您好，请问有什么可以帮助您？\n")
    # 为当前用户初始化一个聊天对象，并开始聊天
    llm_talk(UserTalk())
    
    
def main():
    talk_start()
    

if __name__ == "__main__":
    main()
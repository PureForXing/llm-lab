from pydantic import BaseModel,Field
from openai import OpenAI
from time import sleep
from enum import Enum

MODEL_DEFAULT_NAME = "lmstudio-community/Qwen3.6-no-thinking"
MODEL_DEFAULT_SYSTEM_PROMPT = """
你是工单信息提取助手，根据用户填入的内容，结构化严格提取姓名、情绪、是否需要跟进，如果内容无匹配，则对应字段留空。
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

class EmotionEnum(str,Enum):
    angry = "不满"
    calm = "一般"
    happy = "满意"
    unknown = ""

class UserRecord(BaseModel):
    user_name:str = Field(...,description="用户姓名")
    emotion:EmotionEnum = Field(...,description="用户情绪")
    need_follow:bool = Field(...,description="是否需要跟进")
    


def llm_talk(talk:UserTalk):
    sendMsg = get_user_input(talk)
    if not sendMsg:
        print("那我们下次再聊~\n")   
        return
    try:
        completion = client.chat.completions.parse(
            model=MODEL_DEFAULT_NAME,
            messages=talk.talk_msg,
            response_format = UserRecord
            )
        print_result_info(completion)
        format_assistant_msg(talk,completion.choices[0].message.content)
        # 校验信息是否正确
        res_message =  completion.choices[0].message
        if res_message.refusal:
            print("请求被大模型拒绝")
        else:
            print(f"{res_message.parsed}")
            user_record:UserRecord = res_message.parsed
            if user_record.need_follow:
                print(f"{user_record.user_name},此用户需要跟进，添加到跟进流程中")

    except Exception as e:
        print(f"失败：{e}")
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
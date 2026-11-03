from pydantic import BaseModel,Field
from openai import OpenAI
from time import sleep
import json

MODEL_DEFAULT_NAME = "lmstudio-community/Qwen3.6-no-thinking"
MODEL_DEFAULT_SYSTEM_PROMPT = """
你是一位专业的心理咨询师，需要根据用户的输入和历史对话记录，
来为用户提供心理帮助，语气要亲切委婉，不要质疑指责用户，或者纠正错误。
你可以尝试了解用户的信息，比如年龄，性别，行业等信息。
然后通过开导引导的方式来沟通。鼓励用户积极面对遇到的困难。
"""

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

def format_tool_msg(talk:UserTalk,msg:str,tool_call_id:str):
    talk.talk_msg.append({"role": "tool","tool_call_id":tool_call_id, "content": msg})

def tool_get_location() -> str:
    print("tool_get_location被调用")
    return "成都"

def tool_get_weather(location:str) -> str:
    print("tool_get_weather被调用")
    if not location:
        return {}
    return json.dumps({
        "city":location,
        "temperature": 22,
        "condition": "多云",
        "humidity": 65
        })

TOOLS_INIT = {
    "get_location":tool_get_location,
    "get_weather":tool_get_weather
    }

TOOLS_SCHEAM = [
        {
            "type":"function",
            "function":{
                "name":"get_location",
                "description":"获取用户所在城市"
                }
        },
        {
            "type":"function",
            "function":{
                "name":"get_weather",
                "description":"获取城市的天气状况",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "location":{
                            "type":"string",
                            "description":"要查询的城市"
                            }
                        }
                    },
                "required":["location"]
                }
        }
    ]

def exec_call(talk:UserTalk,tool_calls:any):
    for call in tool_calls:
        call_name = call.function.name
        arguments = json.loads(call.function.arguments or "{}")
        call_id = call.id
        print(f"{call_name},{arguments},{call_id}")
        try:
            # 尝试获取对应的方法
            tool_content = ""
            fn = TOOLS_INIT.get(call_name)
            if fn is None:
                print(f"没有找到工具{call_name}")
                tool_content = f"没有找到工具{call_name}"
            else:
                print(f"开始调用工具{call_name}")
                tool_content = fn(**arguments)
                print(tool_content)

            
        except Exception as e:
            print(f"工具{call_name}调用失败")
            tool_content = f"工具{call_name}调用失败"
            
        format_tool_msg(talk,tool_content,call_id)    

def llm_talk(talk:UserTalk,hasInput:bool=True):
    if hasInput:
        sendMsg = get_user_input(talk)
        if not sendMsg:
            print("那我们下次再聊~\n")   
            return
        
    for i in range(3):
        try:
            completion = client.chat.completions.create(
                model=MODEL_DEFAULT_NAME,
                messages=talk.talk_msg,
                tools=TOOLS_SCHEAM,
                tool_choice="auto",
                stream=False
            )
            # full_msg = []
            # for chunk in completion:
            #     row_msg = chunk.choices[0].delta.content or ""
            #     if row_msg:
            #         print(row_msg,end="",flush=True)
            #         full_msg.append(row_msg)
            # # 组合message
            # full_msg_str = "".join(full_msg)
            # 先获取大模型输出
            assistant_msg = completion.choices[0].message
            
            talk.talk_msg.append(assistant_msg.model_dump(exclude_none=True))
            # 检查是否包含工具调用
            tool_calls = assistant_msg.tool_calls
            if not tool_calls:
                print(assistant_msg)
                break
            # 开始工具调用
            print(tool_calls)
            exec_call(talk,tool_calls)
            # 将工具调用结果返回给大模型
            llm_talk(talk,False)
            break
        except Exception as e:
            print(f"失败：{e},正在重试第{i}次")
            sleep(2*(i+1))
            if i==2:
                print("LLM服务异常")
            
    llm_talk(talk)

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
    
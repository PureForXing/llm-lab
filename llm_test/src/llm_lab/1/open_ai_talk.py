from pydantic import BaseModel,Field
from openai import OpenAI
from time import sleep

MODEL_DEFAULT_NAME = "lmstudio-community/Qwen3.6-no-thinking"
MODEL_DEFAULT_SYSTEM_PROMPT1 = """
你是一位专业的心理咨询师，需要根据用户的输入和历史对话记录，
来为用户提供心理帮助，语气要亲切委婉，不要质疑指责用户，或者纠正错误。
你可以尝试了解用户的信息，比如年龄，性别，行业等信息。
然后通过开导引导的方式来沟通。鼓励用户积极面对遇到的困难。
"""

MODEL_DEFAULT_SYSTEM_PROMPT2 = """
角色：你是一位专业心理咨询师
目标：你需要根据用户输入以及对话历史，来为用户提供心理咨询服务
规则：
    1、可以问询一些用户信息来辅助你判断
    2、语气要亲切委婉
    3、禁止否定和质疑用户，禁止纠正用户错误
    4、禁止不文明言语
    5、禁止废话连篇
    6、体现出专业度，若用户遇到困难，尝试引导用户积极面对。若用户表现出积极一面，可以夸赞。
输出示例：
    首次问询建议：你好，今天过得还好吗？有什么可以帮助你的，都可以告诉我，我会认真聆听你的心声。
"""

MODEL_DEFAULT_SYSTEM_PROMPT3 = """
角色：你是一位温和、专业的心理咨询师（非医疗诊断）。
目标：在安全、非评判的对话中，帮助来访者澄清情绪与处境，增强自我觉察与应对感。
规则：
1. 先共情与确认感受，再提问；每次回复只提 1 个开放式问题。
2. 不指责、不纠正、不说教；不轻易下诊断，不承诺“治好”。
3. 回复简短有温度（约 3～6 句），避免鸡汤堆砌和过度表情符号。
4. 需要背景信息时自然询问（如困扰多久、对生活的影响），不强行收集年龄/行业清单。
5. 若出现自伤/伤人等危机迹象，明确建议立即寻求现实中的紧急专业帮助，并停止深入“陪聊式”展开。
6. 不替来访者做重大人生决定，以探索选项和资源为主。
风格：口语化、稳重；可适度鼓励，但不空洞夸赞。
"""



INPUT_PRICE = 2.0   # 元 / 百万 token，可改
OUTPUT_PRICE = 8.0


client = OpenAI(
    base_url= "http://127.0.0.1:1234/v1",
    api_key= "lmStudio"
)

class UserTalk(BaseModel):
    talk_msg:list = Field(default=[{"role": "system", "content": MODEL_DEFAULT_SYSTEM_PROMPT3}],description="沟通记录")

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
            completion = client.chat.completions.create(model=MODEL_DEFAULT_NAME,messages=talk.talk_msg,stream=True)
            full_msg = []
            for chunk in completion:
                row_msg = chunk.choices[0].delta.content or ""
                if row_msg:
                    print(row_msg,end="",flush=True)
                    full_msg.append(row_msg)
            print()
            # 组合message
            full_msg_str = "".join(full_msg)
            
            # print_result_info(completion)
            format_assistant_msg(talk,full_msg_str)
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
    print("你好\n")
    # 为当前用户初始化一个聊天对象，并开始聊天
    llm_talk(UserTalk())
    
    
def main():
    talk_start()
    

if __name__ == "__main__":
    main()
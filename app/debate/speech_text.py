import json
import os.path

from langchain_core.language_models import BaseChatModel
import io
from app.debate import debate_prompt, roles
from app.common import config

def query_with_history(llm: BaseChatModel,
                       buffer:io.StringIO,
                       speech_records:list[dict[str,str]],
                       query_prompt:str):
    """
    带历史查询
    :param llm: 大模型
    :param buffer:  会话缓冲
    :param speech_records: 对话列表
    :param query_prompt: 查询的prompt
    :return:
    """
    start = False
    answer_buf:io.StringIO =  io.StringIO()
    for message in llm.stream(input=[buffer.getvalue(), query_prompt]):
        if not start:
            buffer.write(query_prompt + "\n")
            print(query_prompt + "\n")
            start = True
        answer_buf.write(message.content)
        buffer.write(message.content)
        print(message.content, end='')
    answer = answer_buf.getvalue()
    index = answer.find("|")
    speecher = answer[0:index]
    content = answer[index+1:]
    speech_records.append({"speecher": speecher.strip(), "content":content.strip()})
    buffer.write("\n\n")
    print("\n")

def generate_speech(llm_name:str, topic:str, pro_side_topic:str, con_side_topic:str,
                    pro_side_roles:list[str], con_side_roles:list[str]):
    """
    生成发言稿
    :param llm_name: 大模型名称
    :param topic: 主题
    :param pro_side_topic: 正方主题
    :param con_side_topic: 反方主题
    :param pro_side_roles: 正方人物
    :param con_side_roles: 反方人物
    :return:
    """
    from app.llm_api.llm import get_llm
    llm = get_llm(llm_name)
    buffer = io.StringIO()
    speech_records = []
    sys_prompt = debate_prompt.debate_start.format(
        topic=topic,
        pro_side_topic=pro_side_topic, pro_side_roles=roles.get_role_prompt(pro_side_roles),
        con_side_topic=con_side_topic, con_side_roles=roles.get_role_prompt(con_side_roles),
        pro_side_role_1=pro_side_roles[0], pro_side_role_2=pro_side_roles[1], pro_side_role_3=pro_side_roles[2],
        con_side_role_1=con_side_roles[0], con_side_role_2=con_side_roles[1], con_side_role_3=con_side_roles[2])
    buffer.write(sys_prompt + "\n")
    print("\n")
    # 开场白
    presider_prologue = (
        f"欢迎来到硅基辩论赛，今天的辩题是：{topic}, 正方的观点是：{pro_side_topic}，反方的观点是：{con_side_topic}。"
        f"下面有请双方辩手：")
    speech_records.append({"speecher": "presider", "content": presider_prologue})
    speak_aside = (
        f"正方一辩：{roles.role_dict[pro_side_roles[0]].introduce()} 。正方二辩：{roles.role_dict[pro_side_roles[1]].introduce()}。正方三辩：{roles.role_dict[pro_side_roles[2]].introduce()}。"
        f"反方一辩：{roles.role_dict[con_side_roles[0]].introduce()}。反方二辩：{roles.role_dict[con_side_roles[1]].introduce()}。反方三辩：{roles.role_dict[con_side_roles[2]].introduce()}")
    speech_records.append({"speecher": "presider", "content": speak_aside})
    step = "start"
    speech_records.append({"speecher": "presider", "content": "双方辩手已经准备好了，那么我宣布本场辩论赛正式开始！请正方一辩进行开场陈词！请反方一辩进行开场陈词"})
    query_prompts = [debate_prompt.debate_pro_1, debate_prompt.debate_con_1]
    for prompt in query_prompts:
        query_with_history(llm=llm, buffer=buffer, speech_records=speech_records, query_prompt=prompt)

    speech_records.append({"speecher": "presider",
                           "content":"时间到！下面进入攻辩环节，双方辩手依次向对方提一个问题并回答，从正方开始！时间到！下面进入到自由辩论环节，双方辩手轮流向对方提问并回答，总计5轮次问答，请从正方开始！"})
    query_prompts = [debate_prompt.debate_pro_2, debate_prompt.debate_con_2_1, debate_prompt.debate_con_2,
                     debate_prompt.debate_pro_2_1]
    for prompt in query_prompts:
        query_with_history(llm=llm, buffer=buffer, speech_records=speech_records, query_prompt=prompt)
    # 历史记录加上自由辩论环节, 默认10轮辩论
    number = 5
    while number >= 1:
        query_with_history(llm=llm, buffer=buffer, speech_records=speech_records,
                           query_prompt=debate_prompt.debate_pro_3)
        query_with_history(llm=llm, buffer=buffer, speech_records=speech_records,
                           query_prompt=debate_prompt.debate_con_3)
        number -= 1
    speech_records.append({"speecher": "presider","content":"时间到！下面进入到总结陈词环节，双方各派出一名辩手进行总结陈词，请从正方开始！"})
    # 进行总结陈词
    summary_prompts = [debate_prompt.debate_pro_4, debate_prompt.debate_con_4]
    for prompt in summary_prompts:
        query_with_history(llm=llm, buffer=buffer, speech_records=speech_records, query_prompt=prompt)

    debate_topic_dir = os.path.join(config.get_data_dir(), "debate",topic)
    os.makedirs(debate_topic_dir, exist_ok=True)
    text_title = os.path.join(debate_topic_dir, "debate.txt")
    with open(text_title, "w+", encoding="utf-8") as fp:
        fp.write(buffer.getvalue())
        print("写入TXT完成")

    json_title = os.path.join(debate_topic_dir, "debate.json")
    with open(json_title, "w+", encoding="utf-8") as fp:
        json.dump(speech_records, fp=fp, ensure_ascii=False, indent=4)
        print("写入JSON完成")

if __name__ == "__main__":
    llm_name = "deepseek-r1" #"qwq-plus"
    pro_side_roles = ["甄嬛", "沈眉庄", "叶澜依"]
    con_side_roles = ["宜修皇后", "祺嫔", "安陵容"]
    topic = "婚后遇到此生挚爱，要不要离婚"
    pro_side_topic = "要离婚"
    con_side_topic = "不离婚"

    generate_speech(llm_name, topic, pro_side_topic, con_side_topic, pro_side_roles, con_side_roles)
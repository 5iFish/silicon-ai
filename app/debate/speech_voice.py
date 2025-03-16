import os, json
from app.common.text_splitter import ChineseRecursiveTextSplitter
from app.comfyui.base import ComfyUI, UploadInfo
from app.comfyui.running_hub import RunningHubComfyUI
from app.debate.roles import role_dict, BaseRole
from app.common import config, api, media
import shutil

def split(topic:str):
    """
    切分辩论稿
    :param topic: 主题
    :return:
    """
    debate_topic_dir = os.path.join(config.get_data_dir(), "debate", topic)
    json_title = os.path.join(debate_topic_dir, "debate.json")
    speech_records = []
    speech_dicts = []
    text_splitter = ChineseRecursiveTextSplitter(chunk_size=120, chunk_overlap=0)
    with open(json_title, "r+", encoding="utf-8") as fp:
        speech_records = json.load(fp)
    for index, speech_record in enumerate(speech_records):
        speecher = speech_record["speecher"]
        content = speech_record["content"]
        sub_contents = text_splitter.split_text(content)
        speech_dict = {}
        speech_dict["speecher"] = speecher
        speech_dict["contents"] = [{"sub_content":sub_content, "convert":[]} for sub_content in sub_contents]
        speech_dicts.append(speech_dict)

    split_debate_json = os.path.join(debate_topic_dir, "debate_split.json")
    with open(split_debate_json, "w+", encoding="utf-8") as fp:
        json.dump(speech_dicts, fp=fp, ensure_ascii=False, indent=4)
        print("写入分段JSON完成")

def to_voice(topic:str):
    """
    文字转语音,可以多次调用减少失败率
    :param topic: 主题
    :return:
    """
    debate_topic_dir = os.path.join(config.get_data_dir(), "debate", topic)
    split_debate_json = os.path.join(debate_topic_dir, "debate_split.json")
    with open(split_debate_json, "r+", encoding="utf-8") as fr:
        debate_split_contents = json.load(fr)
    for content_index, debate_split_content in enumerate(debate_split_contents):
        speecher = debate_split_content["speecher"]
        if speecher not in role_dict or role_dict[speecher].clone_voice is None or role_dict[speecher].clone_voice_text is None or role_dict[speecher].profile_photo is None:
            continue
        contents = debate_split_content["contents"]
        for sub_content_index, content in enumerate(contents):
            sub_content = content["sub_content"]
            convert:str = content["convert"]
            if convert is None or len(convert) == 0:
                comfy_ui = __get_comfy_ui()
                content["sub_content"] = __remove_brackets(sub_content)
                # TODO 后续支持单独针对文字转音频的工作流
                node_info_list = __get_node_info_list(comfy_ui, speecher, content["sub_content"])
                content["convert"] = comfy_ui.run(node_info_list, workflowId = config.get_debate_text2video_workflowId())
                with open(split_debate_json, "w+", encoding="utf-8") as fr:
                    json.dump(debate_split_contents, fp=fr, ensure_ascii=False, indent=4)

def download_video(topic: str):
    debate_topic_dir = os.path.join(config.get_data_dir(), "debate", topic)
    debate_topic_video = os.path.join(debate_topic_dir, "video")
    os.makedirs(debate_topic_video, exist_ok=True)

    split_debate_json = os.path.join(debate_topic_dir, "debate_split.json")

    with open(split_debate_json, "r+", encoding="utf-8") as fr:
        debate_split_contents = json.load(fr)

    for content_index, debate_split_content in enumerate(debate_split_contents):
        speecher = debate_split_content["speecher"]
        contents = debate_split_content["contents"]
        for sub_content_index, content in enumerate(contents):
            if len(content["convert"]) > 0:
                download_info = content["convert"][0]
                download_url = download_info["fileUrl"]
                download_type = download_info["fileType"]
                download_filename = f"{content_index}.{speecher}.{sub_content_index}.{download_type}"
                if not os.path.exists(os.path.join(debate_topic_video, download_filename)):
                    api.get_file(debate_topic_video, download_filename, download_url)

def combine_video(topic:str):
    debate_topic_dir = os.path.join(config.get_data_dir(), "debate", topic)
    debate_topic_video = os.path.join(debate_topic_dir, "video")
    combine_dir = os.path.join(debate_topic_dir, "video_combine")
    os.makedirs(combine_dir, exist_ok=True)
    combine_dict = {}
    for file in os.listdir(debate_topic_video):
        filename, file_extension = os.path.splitext(file)
        if file_extension == ".mp4":
            combine_name, order = os.path.splitext(filename)
            combine_full_name = combine_name + file_extension
            order = order[1:]
            if combine_full_name not in combine_dict:
                combine_dict[combine_full_name] = []

            combine_dict[combine_full_name].append({
                "path": os.path.join(debate_topic_video, file),
                "order": int(order)
            })

    for combine_file in combine_dict:
        if len(combine_dict[combine_file]) > 1:
            combine_file_sorted = sorted(combine_dict[combine_file], key=lambda info: info["order"])
            combine_filepaths = [combine_obj["path"] for combine_obj in combine_file_sorted]
            media.combine_video(combine_filepaths, combine_dir, combine_file)
        else:
            shutil.copy(combine_dict[combine_file][0]["path"], os.path.join(combine_dir, combine_file))

def __get_node_info_list(comfy_ui: ComfyUI, speecher:str, sub_content:str) -> list[dict]:
    role: BaseRole = role_dict[speecher]
    instruct_bool = False
    instruct_str = ""
    if role.timbre:
        if "instruct_str" in role.timbre:
            instruct_bool = True
            instruct_str = role.timbre.get("instruct_str")
    upload_info_dict = {}
    upload_voice_key:str = "debate:" + role.name + "|voice"
    upload_info_dict[upload_voice_key] = UploadInfo(file_path=role.clone_voice, desc=role.clone_voice_text)
    upload_photo_key:str = "debate:" + role.name + "|profile_photo"
    upload_info_dict[upload_photo_key] = UploadInfo(file_path=role.profile_photo)
    uploaded_info_dict = comfy_ui.upload(upload_info_dict)

    clone_voice = uploaded_info_dict[upload_voice_key].upload_id
    clone_voice_text = uploaded_info_dict[upload_voice_key].desc
    profile_photo = uploaded_info_dict[upload_photo_key].upload_id

    return [
        # 输入文本节点
        {
            "nodeId": "122",
            "fieldName": "text",
            "fieldValue": sub_content
        },
        # 语速节点
        {
            "nodeId": "82",
            "fieldName": "text",
            "fieldValue": "1.0"
        },
        # 是否启用指令控制节点
        {
            "nodeId": "84",
            "fieldName": "text",
            "fieldValue": str(instruct_bool)
        },
        # 指令文本
        {
            "nodeId": "60",
            "fieldName": "text",
            "fieldValue": instruct_str
        },
        # 克隆音频节点
        {
            "nodeId": "6",
            "fieldName": "audio",
            "fieldValue": clone_voice
        },
        # 克隆音频对应文本节点
        {
            "nodeId": "8",
            "fieldName": "text",
            "fieldValue": clone_voice_text
        },
        # 加载数字人节点
        {
            "nodeId": "10",
            "fieldName": "image",
            "fieldValue": profile_photo
        }
    ]


def __get_comfy_ui() -> ComfyUI:
    """
    获取comfyui实例
    :return:
    """
    return RunningHubComfyUI.get_comfy_ui()


def __remove_brackets(text:str) -> str:
    stack_en = 0  # 跟踪英文括号深度
    stack_cn = 0  # 跟踪中文括号深度
    result = []
    for char in text:
        if char == '(':
            stack_en += 1
        elif char == ')':
            if stack_en > 0:
                stack_en -= 1
        elif char == '（':
            stack_cn += 1
        elif char == '）':
            if stack_cn > 0:
                stack_cn -= 1
        else:
            if stack_en == 0 and stack_cn == 0:
                result.append(char)
    return ''.join(result)

if __name__ == "__main__":
    # split("婚后遇到此生挚爱，要不要离婚")
    # for i in range(0, 3):
    #     to_voice("婚后遇到此生挚爱，要不要离婚")
    # download_video("婚后遇到此生挚爱，要不要离婚")
    combine_video("婚后遇到此生挚爱，要不要离婚")
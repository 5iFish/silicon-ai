
from app.debate import speech_text
from app.debate import speech_voice

if __name__ == "__main__":
    llm_name = "deepseek-r1"  # "qwq-plus"
    pro_side_roles = ["甄嬛", "沈眉庄", "叶澜依"]
    con_side_roles = ["宜修皇后", "祺嫔", "安陵容"]
    topic = "婚后遇到此生挚爱，要不要离婚"
    pro_side_topic = "要离婚"
    con_side_topic = "不离婚"

    # 辩论赛文本稿件生成
    speech_text.generate_speech(llm_name, topic, pro_side_topic, con_side_topic, pro_side_roles, con_side_roles)

    # 按照标点切分文本
    speech_voice.split(topic)

    # 通过comfyui将文本转语音驱动的视频，添加3次重试机制
    for i in range(0, 3):
        speech_voice.to_voice(topic)

    # 下载视频
    speech_voice.download_video(topic)

    # 合并下载好的视频
    speech_voice.combine_video(topic)
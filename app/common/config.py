import os
from configparser import ConfigParser

_cf = ConfigParser()
_cf.read(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.ini"))

def get_value(section, option) -> str:
    """获取指定配置信息"""
    return _cf.get(section, option)

def get_data_dir():
    """获取数据文件夹"""
    silicon_ai_data =  os.getenv("SILICON_AI_DATA")
    if not silicon_ai_data:
        silicon_ai_data = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    if not os.path.exists(silicon_ai_data):
        os.makedirs(silicon_ai_data, exist_ok=True)
    return silicon_ai_data

def get_debate_text2video_workflowId():
    return int(get_value("running_hub", "debate_text2video_workflowId"))

def get_debate_text2voice_workflowId():
    return int(get_value("running_hub", "debate_text2voice_workflowId"))
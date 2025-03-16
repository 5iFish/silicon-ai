import os.path

from requests import Response
import json
from app.common.logger import log
import requests
from app.common import config

def get_proxy() -> dict[str, str]:
    http_proxy = config.get_value("proxy", "http_proxy")
    https_proxy = config.get_value("proxy", "https_proxy")

    if http_proxy is None or http_proxy == "":
        if https_proxy is None or https_proxy == "":
            return {}
        else:
            return {"https": https_proxy}
    else:
        if https_proxy is None or https_proxy == "":
            return {"http": http_proxy}
        else:
            return {"http": http_proxy, "https": https_proxy}

def get_file(download_dir, download_file_name, file_link):
    """
    下载文件
    :param download_dir: 本地文件夹
    :param download_file_name: 下载文件名称
    :param file_link: 文件链接地址
    :return:
    """
    log.info("开始下载文件:" + download_file_name)
    r = requests.get(file_link, proxies=get_proxy(), stream=True).iter_content(chunk_size=1024 * 1024)
    with open(os.path.join(download_dir, download_file_name), 'wb') as f:
        for chunk in r:
            if chunk:
                f.write(chunk)
    log.info("完成文件下载:" + download_file_name)

def upload_file(file_path:str, upload_api:str, data_dict) -> Response:
    """
    上传文件
    :param file_path: 文件路径
    :param upload_api: 上传的地址
    :param data_dict: 载荷数据
    :return: 返回相应信息
    """
    response = requests.post(upload_api, data=data_dict, files={"file": open(file_path, "rb")}, timeout=30)
    return response

def post(url, headers, data_dict):
    response = requests.post(url=url, headers=headers, data=json.dumps(data_dict, ensure_ascii=False).encode("utf-8"), timeout=30)
    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError("Post请求失败!")

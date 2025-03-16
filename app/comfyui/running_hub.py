from app.comfyui.base import ComfyUI
import os
from app.common import dao, file, api
from app.common.logger import log
from time import sleep
from app.comfyui.base import UploadInfo

class RunningHubComfyUI(ComfyUI):

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.runninghub.cn"
        """基础的api"""
        self.api_key = os.getenv('RUNNING_HUB_API_KEY')
        """Running Hub的API接口"""
        self.task_upload_api="/task/openapi/upload"
        """上传接口"""
        self.task_run_api="/task/openapi/create"
        """执行工作流的API"""
        self.task_status_api = "/task/openapi/status"
        """获取工作流执行状态"""
        self.task_output_api = "/task/openapi/outputs"
        """获取执行输出结果接口"""
        self.running_hub_tab = "running_hub_cache"
        """缓存的表名"""
        self.__init_db()
        """初始化表"""

    def run(self, node_info_list:list, **kw):
        """
        执行工作流
        :param node_info_list: 保存文件夹
        :param kw: 键值对，必须包含workflowId
        """
        headers = {
            "Content-Type": "application/json",
            "Host": "www.runninghub.cn"
        }
        data = {
            "workflowId": kw["workflowId"],
            "apiKey": self.api_key,
            "nodeInfoList": node_info_list
        }

        response_dict = api.post(self.base_url + self.task_run_api, headers=headers, data_dict=data)
        task_id = ""
        if response_dict["msg"] == "success":
            task_id = response_dict["data"]["taskId"]
        else:
            raise RuntimeError("创建工作流任务不成功：" + response_dict["msg"])
        if task_id == "":
            return []

        log.info("创建工作流任务成功：" + task_id)

        error_time = 0
        task_state = ""
        while True:
            # 休眠30s
            sleep(30)
            task_state = self.__get_task_state(task_id)
            if task_state == "":
                error_time += 1
                if error_time > 3:
                    log.error("工作流任务执行失败：" + task_id)
                    return []
            elif error_time != 0:
                error_time = 0

            if task_state == "SUCCESS" or task_state == "FAILED":
                break

        if task_state == "SUCCESS":
            log.info("工作流任务执行成功：" + task_id)
            return self.__get_task_output(task_id)

        log.error("工作流任务执行失败：" + task_id)
        return []

    def __get_task_state(self,task_id: str):
        """
        返回任务状态
        :param task_id: 任务id
        :return: 返回任务状态
        """
        headers = {
            "Content-Type": "application/json",
            "Host": "www.runninghub.cn"
        }
        data = {
            "taskId": task_id,
            "apiKey": self.api_key
        }
        response_dict = api.post(self.base_url + self.task_status_api, headers, data)
        if response_dict["msg"] == "success":
            return response_dict["data"]
        else:
            return ""

    def __get_task_output(self,task_id: str):
        """
        获取任务输出结果
        :param task_id: 任务id
        :return:
        """
        headers = {
            "Content-Type": "application/json",
            "Host": "www.runninghub.cn"
        }
        data = {
            "taskId": task_id,
            "apiKey": self.api_key
        }

        response_dict = api.post(self.base_url + self.task_output_api, headers, data)
        if response_dict["msg"] == "success":
            return response_dict["data"]
        else:
            return []

    def upload(self, upload_dict:dict[str, UploadInfo]) -> dict[str, UploadInfo]:
        """上传"""
        upload_info_dict = {}
        for full_name in upload_dict:
            """遍历上传的文件，如果在缓存中没有找到则上传并创建上传记录到缓存库中"""
            raw_upload_info = upload_dict[full_name]
            file_path = raw_upload_info.file_path
            file_md5 = file.get_file_md5(file_path)
            namespace_index = full_name.index(":")
            namespace = ""
            local_name = full_name
            if namespace_index != -1:
                namespace = full_name[0:namespace_index]
                local_name = full_name[namespace_index + 1:]
            upload_info = self.__get_upload_cache(namespace, local_name, file_path, file_md5)
            if upload_info is None:
                upload_id = self.__upload_file(namespace, local_name, file_path, file_md5, raw_upload_info.desc)
                upload_info = UploadInfo(file_path = file_path, upload_id=upload_id, desc=raw_upload_info.desc)
            else:
                log.info("文件已存在，无需上传：" + full_name)
            upload_info_dict[full_name] = upload_info
        return upload_info_dict

    def __upload_file(self, namespace:str, local_name:str, file_path:str, file_md5:str, desc:str) -> str:
        """
        更新文件
        :param full_name: 完整名称
        :param file_path: 文件路径
        :param file_md5: 文件md5值
        :return: 返回上传的id
        """
        response = api.upload_file(file_path, self.base_url + self.task_upload_api,
                        {"fileType":self.__get_file_type(file_path), "apiKey": self.api_key})
        if response.status_code == 200:
            response_dict = response.json()
            if response_dict["msg"] == "success":
                log.info("上传成功：" + file_path + " -> " + response_dict["data"]["fileName"])
                dao.execute(f"replace into {self.running_hub_tab} (namespace, local_name, upload_id, obj_md5, desc) values "
                            f"('{namespace}', '{local_name}', '{response_dict["data"]["fileName"]}', '{file_md5}', '{desc}')")
                return response_dict["data"]["fileName"]
            else:
                raise RuntimeError("上传失败:" + file_path)
        else:
            raise RuntimeError("上传失败:" + file_path)

    def __get_file_type(self, file_path:str):
        ext = os.path.splitext(file_path)[-1]
        if ext.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            return "image"
        if ext.lower() in [".mp3", ".wav", ".flac", ".aac"]:
            return "audio"
        raise RuntimeError("无法识别文件类型：" + file_path)

    def __get_upload_cache(self, namespace:str, local_name:str, file_path:str, file_md5:str) -> UploadInfo | None:
        """获取指定key的缓存信息"""

        upload_info = dao.query(f"select upload_id, desc, obj_md5 from {self.running_hub_tab} where namespace='{namespace}' and local_name='{local_name}'")

        if upload_info:
            if upload_info["obj_md5"] == "":
                dao.execute(f"update {self.running_hub_tab} set obj_md5='{file_md5}' where namespace='{namespace}' and local_name='{local_name}'")
                upload_info["obj_md5"] = file_md5
            if upload_info["obj_md5"] == file_md5:
                return UploadInfo(file_path = file_path, upload_id=upload_info["upload_id"], desc=upload_info["desc"])


    def __init_db(self):
        """创建表"""
        create_sql = f"create table if not exists {self.running_hub_tab} (namespace TEXT, local_name TEXT, upload_id TEXT, obj_md5 str, desc TEXT, primary key (namespace, local_name))"
        dao.execute(create_sql)

    @classmethod
    def get_comfy_ui(cls) -> ComfyUI:
        return cls()

from typing import Optional


class UploadInfo:

    def __init__(self, file_path:Optional[str] = None, upload_id:Optional[str] = None, desc:Optional[str] = None):
        self.file_path = "" if file_path is None else file_path
        self.upload_id = "" if upload_id is None else upload_id
        self.desc = "" if desc is None else desc

class ComfyUI:

    def __init__(self, *args, **kw):
        """初始化参数"""

    def run(self, node_info_list:list, *args, **kw):
        """执行工作流并获取执行结果"""

    def upload(self, upload_dict: dict[str, UploadInfo]) -> dict[str, UploadInfo]:
        """相关文件上传接口"""
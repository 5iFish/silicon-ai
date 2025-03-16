import json, os
from typing import Optional, Any, List
from uuid import UUID
from app.common.logger import log

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.callbacks import LLMManagerMixin, Callbacks, BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import LLMResult


class TongyiTokenResult(BaseCallbackHandler):
    """统计使用的token"""

    def on_llm_end(
            self,
            response: LLMResult,
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
    ) -> Any:
        tokens = response.generations[0][0].message.response_metadata['token_usage']
        log.info(f"输入token：{tokens["input_tokens"]}, 输出token：{tokens["output_tokens"]}, 总token：{tokens["total_tokens"]}")

class TongyiApi:
    """封装tongyi的api"""

    def __init__(self, model_name):
        """
        初始化
        :param model_name: 设置模型名称
        """
        self.model = model_name
        self.api_key = os.getenv('TONGYI_API_KEY')
        self.token_result = TongyiTokenResult()

    def get_llm(self):
        """
        获取大模型
        :return: 获取模型
        """
        return ChatTongyi(api_key=self.api_key, model=self.model, callbacks=[self.token_result])


llm_dict = {
    "deepseek-r1": TongyiApi(model_name="deepseek-r1").get_llm(),
    "deepseek-v3": TongyiApi(model_name="deepseek-v3").get_llm(),
    "qwen-plus": TongyiApi(model_name="qwen-plus").get_llm(),
    "qwq-32b": TongyiApi(model_name="qwq-32b").get_llm(),
    "qwq-plus": TongyiApi(model_name="qwq-plus").get_llm(),
    "qwen-max": TongyiApi(model_name="qwen-max").get_llm()
}

def get_llm(model_name:str) -> BaseChatModel:
    """
    通过模型名称获取模型
    :param model_name: 模型名称
    :return:
    """
    return llm_dict[model_name]
import logging

LOGGER_INFO = ""

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(module)s:%(lineno)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def get_logger(log_name):
    """
    获取全局的logger
    :param log_name: 日志名称
    :return: 返回日志对象
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    return logger

log = get_logger("silicon-ai")
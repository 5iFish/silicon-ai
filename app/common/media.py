import os.path
from moviepy import VideoFileClip, concatenate_videoclips
from app.common.logger import log

support_video_type = [".mp4"] # 配置支持的视频后缀，当前仅添加了mp4格式

def combine_video(video_paths:list[str], combine_dir:str, combine_name:str):
    """
    合并视频
    :param video_paths: 待合并视频路径列表
    :param combine_dir: 合并后输出文件夹名称
    :param combine_name: 合并后输出文件名称
    :return:
    """
    videos = []
    for video_path in video_paths:
        if os.path.splitext(video_path)[1] in support_video_type:
            videos.append(VideoFileClip(video_path))

    combine_result = concatenate_videoclips(videos)
    combine_result.write_videofile(os.path.join(combine_dir, combine_name))

    log.info(f"合并视频 {combine_name} 成功!")

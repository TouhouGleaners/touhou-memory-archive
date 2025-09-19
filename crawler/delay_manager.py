from random import random
from typing import Optional

class DelayManager:
    _instance: Optional['DelayManager'] = None
    
    def __init__(self):
        self.last_user_video_count: int = 0
        self.base_delay: float = 1.0
    
    @classmethod
    def get_instance(cls) -> 'DelayManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def update_video_count(self, count: int) -> None:
        """更新上一个用户的视频数量"""
        self.last_user_video_count = count
    
    def get_user_switch_delay(self) -> float:
        """获取用户切换时的延迟时间"""
        delay = calculate_dynamic_delay(self.last_user_video_count)
        return delay + random()  # 添加随机波动


def calculate_dynamic_delay(video_count: int) -> float:
    """动态计算用户间延迟时间"""
    if video_count <= 10:
        return 0.0 + random() * 5  # 0~5
    if video_count <= 50:
        return 5.0 + random() * 10  # 5~15
    if video_count <= 100:
        return 10.0 + random() * 15  # 10~25
    if video_count <= 250:
        return 15.0 + random() * 20  # 15~35
    if video_count <= 500:
        return 20.0 + random() * 25 # 20~45
    return 60.0 + random() * 30 # 60~90
    
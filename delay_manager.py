import math
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
    """
    根据上一个用户的视频数量动态计算下一个用户的延迟时间
    
    Args:
        video_count: 上一个用户的视频总数
        base_delay: 基础延迟时间（秒）
    
    Returns:
        float: 计算得到的延迟时间（秒）
        
    计算逻辑:
    1. 视频数量 <= 10: 使用基础延迟
    2. 视频数量 10-50: 延迟线性增加
    3. 视频数量 > 50: 使用对数增长避免延迟过大
    """
    if video_count <= 50:
        return 3.0 + random()
    elif video_count <= 200:
        return 5.0 + random()
    else:
        return 8.0 + random()

import logging
from random import uniform
from typing import Optional

from config import USER_SWITCH_CONFIG

logger = logging.getLogger(__name__)

class DelayManager:
    """用户间延迟管理类"""
    _instance: Optional['DelayManager'] = None
    
    def __init__(self):
        self.last_user_video_count: int = 0
        self.config = USER_SWITCH_CONFIG
    
    @classmethod
    def get_instance(cls) -> 'DelayManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def update_video_count(self, count: int) -> None:
        """在处理完一个用户后，更新该用户的视频数量"""
        self.last_user_video_count = count
    
    def get_user_switch_delay(self) -> float:
        """获取用户切换时的延迟时间"""
        dynamic_delay = self.last_user_video_count * self.config['FACTOR_PER_VIDEO']
        base_plus_dynamic = self.config['BASE_DELAY'] + dynamic_delay
        capped_delay = min(base_plus_dynamic, self.config['MAX_DELAY'])
        jitter = capped_delay * self.config['JITTER_RATIO']
        final_delay = max(0, capped_delay + uniform(-jitter, jitter))

        logger.debug(
            f"上个用户视频数: {self.last_user_video_count}, "
            f"计算延迟: [基础:{self.config['BASE_DELAY']:.1f}s] + [动态:{dynamic_delay:.1f}s] -> "
            f"[应用上限后:{capped_delay:.1f}s] ± [抖动:{jitter:.1f}s] -> "
            f"最终等待: {final_delay:.2f} 秒"
        )

        return final_delay
import asyncio
import logging
from typing import Any

import aiohttp

from crawler.config import HEADERS
from crawler.core.delay_manager import DelayManager

from .wbi_signer import WbiSigner


logger = logging.getLogger(__name__)


class BiliAPI:
    """与 B 站服务器通信类"""
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def request(
        self,
        url: str,
        params: dict[str, Any] = None,
        *,
        need_wbi: bool = False,
        headers: dict = None,
        retry_times: int = 3,
        retry_delay: int = 5
    ) -> dict:
        """
        公共 API 请求函数
        
        Args:
            url: API 地址
            params: 请求参数
            need_wbi: 是否需要 WBI 签名
            headers: 特殊的headers
            retry_times: 最大重试次数
            retry_delay: 重试延迟基础时间（秒）
        
        Returns:
            经过 process_data 处理后的数据
        
        Raises:
            Exception: API 请求失败或数据处理出错
        """
        params = params or {}
        req_headers = HEADERS.copy()

        if headers:
            req_headers.update(headers)

        if need_wbi:
            img, sub = WbiSigner.get_wbi_keys()
            params = WbiSigner.enc_wbi(params, img, sub)

        for attempt in range(retry_times):
            is_last_attempt = attempt == retry_times - 1
            current_delay = retry_delay * (attempt + 1)

            try:
                async with self.session.get(url=url, params=params, headers=req_headers) as response:
                    # 风控处理
                    if response.status == 412:
                        if is_last_attempt:
                            raise Exception(f"API请求失败: 触发风控(412)，重试次数耗尽")
                        logger.warning(f"请求过快触发风控，等待 {current_delay} 秒后重试")
                        await asyncio.sleep(current_delay)
                        continue

                    response.raise_for_status()

                    data = await response.json()
                    if data.get('code') != 0:
                        raise Exception(f"API返回错误: {data.get('message', '未知错误')}")
                    
                    return data.get('data', {})
                
            except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
                if not is_last_attempt:
                    logger.warning(f"请求失败，等待 {current_delay} 秒后重试: {str(e)}")
                    await asyncio.sleep(current_delay)
                    continue
                raise Exception(f"API请求失败: {str(e)}") from e
            
            except Exception as e:
                if not is_last_attempt:
                    logger.warning(f"数据处理失败，等待 {current_delay} 秒后重试: {str(e)}")
                    await asyncio.sleep(current_delay)
                    continue
                raise Exception(f"数据处理失败: {str(e)}") from e
            finally:
                sleep_time = DelayManager.get_instance().get_request_delay()
                await asyncio.sleep(sleep_time)

    async def get_user_video_list(self, mid: int, pn: int, ps: int) -> dict:
        """获取用户空间的视频列表"""
        return await self.request(
            url="https://api.bilibili.com/x/space/wbi/arc/search",
            params={'mid': mid, 'pn': pn, 'ps': ps},
            need_wbi=True
        )
    
    async def get_season_video_list(self, mid: int, season_id: int, pn: int, ps: int) -> dict:
        """获取合集/系列的视频列表"""
        headers = {'Referer': f'https://space.bilibili.com/{mid}/lists/{season_id}?type=season'}
        return await self.request(
            "https://api.bilibili.com/x/polymer/web-space/seasons_archives_list",
            params={'mid': mid, 'season_id': season_id, 'page_num': pn, 'page_size': ps},
            headers=headers
        )
    
    async def get_video_detail(self, bvid: str) -> dict:
        """获取视频详细信息（简介、统计数据等）"""
        return await self.request(
            "https://api.bilibili.com/x/web-interface/view",
            params={'bvid': bvid}
        )
    
    async def get_video_parts(self, bvid: str) -> dict:
        """获取视频的分P列表"""
        return await self.request(
            "https://api.bilibili.com/x/player/pagelist",
            params={'bvid': bvid}
        )
    
    async def get_video_tags(self, bvid: str) -> dict:
        """获取视频的标签列表"""
        return await self.request(
            "https://api.bilibili.com/x/web-interface/view/detail/tag",
            params={'bvid': bvid}
        )
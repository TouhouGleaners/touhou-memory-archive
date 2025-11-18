import asyncio
import aiohttp
import logging
from typing import Callable, TypeVar, Any

from .config import HEADERS, DELAY_SECONDS, PRODUCER_PAGE_DELAY_SECONDS
from .delay_manager import DelayManager
from .video import Video, VideoPart
from .wbi_signer import WbiSigner


logger = logging.getLogger(__name__)

T = TypeVar('T')

class PageFetchExhaustedError(Exception):
    """当获取单个页面在多次重试后仍然失败时抛出"""
    pass


class BiliApiClient:
    """封装所有与 Bilibili API 交互的客户端"""
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def _make_request(
        self,
        url: str,
        params: dict[str, Any],
        process_data: Callable[[dict[str, Any]], T],
        *,
        need_wbi: bool = False,
        retry_times: int = 3,
        retry_delay: int = 5,
        delay_seconds: Callable[[], float] = DELAY_SECONDS,
    ) -> T:
        """
        公共 API 请求函数
        
        Args:
            url: API 地址
            params: 请求参数
            need_wbi: 是否需要 WBI 签名
            retry_times: 最大重试次数
            retry_delay: 重试延迟基础时间（秒）
            process_data: 处理返回数据的函数
            delay_seconds: 请求延迟函数
        
        Returns:
            经过 process_data 处理后的数据
        
        Raises:
            Exception: API 请求失败或数据处理出错
        """
        if need_wbi:
            img_key, sub_key = await WbiSigner.get_wbi_keys()
            params = WbiSigner.enc_wbi(params, img_key, sub_key)
        
        for attempt in range(retry_times):
            try:
                async with self.session.get(url=url, params=params, headers=HEADERS) as response:
                    # 处理风控
                    if response.status == 412:
                        logger.warning(f"请求过快触发风控，等待 {retry_delay * (attempt + 1)} 秒后重试")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    
                    response.raise_for_status()  # 处理其他HTTP错误
                    
                    data = await response.json()
                    if data.get('code') != 0:
                        raise Exception(f"API返回错误: {data.get('message', '未知错误')}")
                    
                    return process_data(data)
                
            except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
                if attempt < retry_times - 1:
                    logger.warning(f"请求失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {str(e)}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception(f"API请求失败: {str(e)}")
            
            except Exception as e:
                if attempt < retry_times - 1:
                    logger.warning(f"数据处理失败，等待 {retry_delay * (attempt + 1)} 秒后重试: {str(e)}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                raise
            finally:
                await asyncio.sleep(delay_seconds())

    async def get_season_videos(self, mid: int, season_id: int) -> list[Video]:
        """根据mid和season_id获取并返回一个合集中的所有视频"""
        logger.info(f"发现合集 season_id={season_id}，正在获取其内部视频...")

        all_videos = []
        page_num = 1
        page_size = 50

        # 构造API需要的特定Referer
        referer_url = f'https://space.bilibili.com/{mid}/lists/{season_id}?type=season'
        request_headers = HEADERS.copy()
        request_headers['Referer'] = referer_url

        while True:
            params = {'mid': mid, 'season_id': season_id, 'page_num': page_num, 'page_size': page_size}
            
            try:
                async with self.session.get(
                    "https://api.bilibili.com/x/polymer/web-space/seasons_archives_list",
                    params=params,
                    headers=request_headers
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data.get('code') != 0:
                        raise Exception(f"合集API返回错误: {data.get('message', '未知错误')}")
                    
                    archives: list = data.get('data', {}).get('archives', [])
                    if not archives:
                        break

                    for archive_data in archives:
                        archive_data['mid'] = mid
                        archive_data['season_id'] = season_id
                        try:
                            all_videos.append(Video.model_validate(archive_data))
                        except Exception as e:
                            bvid = archive_data.get('bvid', '未知bvid')
                            logger.warning(f"解析合集内视频 {bvid} 数据失败，跳过: {e}")

                    # 检查是否还有更多页面
                    total_videos = data.get('data', {}).get('meta', {}).get('total', 0)
                    if len(all_videos) >= total_videos:
                        break # 已获取的视频数等于或超过总数，停止循环

                    page_num += 1
                    await asyncio.sleep(DELAY_SECONDS())

            except Exception as e:
                logger.error(f"获取合集 season_id={season_id} 第 {page_num} 页失败: {e}")
                return all_videos
            
        logger.info(f"合集 season_id={season_id} 获取完成，共 {len(all_videos)} 个视频。")
        return all_videos

    async def _fetch_video_page(self, mid: int, page_num: int, page_size: int) -> dict:
        """获取单页视频"""
        params = {'mid': mid, 'pn': page_num, 'ps': page_size}

        def process_video_page(data: dict[str, Any]) -> dict:
            vlist = data['data']['list']['vlist']
            total_videos = data['data']['page']['count']
            page_videos = [Video.model_validate(video) for video in vlist if video]
            return {'page': page_num, 'total': total_videos, 'videos': page_videos}

        return await self._make_request(
            url="https://api.bilibili.com/x/space/wbi/arc/search",
            params=params,
            process_data=process_video_page,
            need_wbi=True,
        )

    async def _fetch_page_with_retry(self, mid: int, page_num: int, page_size: int) -> dict:
        """
        获取单个视频列表页面，并内置长间隔的业务重试逻辑
        成功则返回页面结果，重试耗尽后则抛出 PageFetchExhaustedError
        """
        max_retries = 3
        base_retry_delay = 30
        for attempt in range(max_retries):
            try:
                return await self._fetch_video_page(mid, page_num, page_size)
            except Exception as e:
                logger.error(f"获取用户 {mid} 第 {page_num} 页时出错 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    retry_delay = base_retry_delay * (attempt + 1)
                    logger.info(f"等待 {retry_delay} 秒后继续尝试...")
                    await asyncio.sleep(retry_delay)
        raise PageFetchExhaustedError(f"用户 {mid} 的第 {page_num} 页在 {max_retries} 次尝试后仍然获取失败")
        

    async def get_user_all_videos(
        self,
        mid: int,
        queue: asyncio.Queue,
        delay_manager: DelayManager,
        page_size: int = 50
    ) -> None:
        """生产者：获取用户所有视频，处理合集视频，并放入队列"""
        processed_seasons = set()
        try:
            # 获取第一页以确认总页数，避免不必要请求
            first_page = await self._fetch_page_with_retry(mid, 1, page_size)
            total_videos = first_page['total']
            total_pages = (total_videos + page_size - 1 ) // page_size

            delay_manager.update_video_count(total_videos)

            logger.info(f"用户 {mid} 所有视频列表获取任务启动：共 {total_videos} 个视频，分 {total_pages} 页")
            
            for video in first_page['videos']:
                if video.season_id and video.season_id not in processed_seasons:
                    processed_seasons.add(video.season_id)
                    season_videos = await self.get_season_videos(mid, video.season_id)
                    for season_video in season_videos:
                        await queue.put(season_video)
                elif not video.season_id:
                    await queue.put(video)

        except (PageFetchExhaustedError, Exception) as e:
            logger.critical(f"获取用户 {mid} 初始信息失败，任务中止: {str(e)}")
            return
        
        if total_pages <= 1:
            logger.info(f"用户 {mid} 的所有视频列表（包括合集）均已放入队列(只有一页)")
            return
        
        # 从第二页开始获取
        for page_num in range(2, total_pages + 1):
            try:
                await asyncio.sleep(PRODUCER_PAGE_DELAY_SECONDS)
                page_result = await self._fetch_page_with_retry(mid, page_num, page_size)

                for video in page_result.get('videos', []):
                    if video.season_id and video.season_id not in processed_seasons:
                        processed_seasons.add(video.season_id)
                        season_videos = await self.get_season_videos(mid, video.season_id)
                        for season_video in season_videos:
                            await queue.put(season_video)
                    elif not video.season_id:
                        await queue.put(video)

            except PageFetchExhaustedError as e:
                logger.critical(f"发生严重错误: {e}, 中止对用户 {mid} 的处理")
                return

        logger.info(f"用户 {mid} 的所有视频列表均已放入队列")

    async def get_video_parts(self, bvid: str) -> list[VideoPart]:
        """获取单个视频的分P信息"""
        def process_parts(data: dict[str, Any]) -> list[VideoPart]:
            return [VideoPart.model_validate(p) for p in data.get('data', [])]
            
        return await self._make_request(
            url="https://api.bilibili.com/x/player/pagelist",
            params={'bvid': bvid},
            process_data=process_parts
        )
        
    async def get_video_tags(self, bvid: str) -> list[str]:
        """获取单个视频的标签信息"""
        def process_tags(data: dict[str, Any]) -> list[str]:
            return [tag['tag_name'] for tag in data.get('data', [])]
        
        return await self._make_request(
            url="https://api.bilibili.com/x/web-interface/view/detail/tag",
            params={'bvid': bvid},
            process_data=process_tags
        )
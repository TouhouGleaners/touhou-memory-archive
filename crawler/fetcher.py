import asyncio
import aiohttp
import logging
from tqdm.asyncio import tqdm_asyncio
from typing import Callable, TypeVar, Dict, List, Tuple, Any

from config import HEADERS, DELAY_SECONDS, BATCH_FETCH_CONFIG
from delay_manager import DelayManager
from video import Video, VideoPart
from wbi_signer import WbiSigner


logger = logging.getLogger(__name__)

T = TypeVar('T')

async def make_api_request(
    url: str,
    params: Dict[str, Any],
    *,
    need_wbi: bool = False,
    retry_times: int = 3,
    retry_delay: int = 5,
    process_data: Callable[[Dict[str, Any]], T],
    session: aiohttp.ClientSession,
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
        img_key, sub_key = WbiSigner.get_wbi_keys()
        params = WbiSigner.enc_wbi(params, img_key, sub_key)
    
    for attempt in range(retry_times):
        try:
            async with session.get(url=url, params=params, headers=HEADERS) as response:
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


async def fetch_video_page(mid: int, session: aiohttp.ClientSession, page_number: int, page_size: int, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> dict:
    """获取单页视频"""
    params = {'mid': mid, 'pn': page_number, 'ps': page_size}

    def process_video_page(data: Dict[str, Any]) -> dict:
        vlist = data['data']['list']['vlist']
        total_videos = data['data']['page']['count']

        page_videos = []
        for item in vlist:
            try:
                page_videos.append(Video(item))
            except Exception as e:
                logger.warning(f"视频 {item.get('bvid')} 数据解析错误: {e}")
        return {'page': page_number, 'total': total_videos, 'videos': page_videos}

    return await make_api_request(
        url="https://api.bilibili.com/x/space/wbi/arc/search",
        params=params,
        need_wbi=True,
        process_data=process_video_page,
        session=session,
        delay_seconds=delay_seconds,
    )

async def fetch_video_list(mid: int, session: aiohttp.ClientSession, page_size: int = 50, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[Video]:
    """获取用户所有视频列表"""
    try:
        # 获取第一页以确认总页数，避免不必要请求
        first_page = await fetch_video_page(mid, session, 1, page_size, delay_seconds)
        total_videos = first_page['total']
        total_pages = (total_videos + page_size - 1 ) // page_size
        
        DelayManager.get_instance().update_video_count(total_videos)  # 更新上一个用户的视频数量，用于后续的延迟计算
        
        all_videos = first_page['videos']

        # 如果只有一页，直接返回
        if total_pages == 1:
            return all_videos

    except Exception as e:
        logger.error(f"获取用户 {mid} 视频列表失败: {str(e)}")
        return []
    
    # 为后续页面请求创建一个有限的并发控制器
    # 并发请求应该尽可能的小，以模拟用户快速翻页
    list_semaphore = asyncio.Semaphore(2)
    async def fetch_page_with_semaphore(page_num):
        async with list_semaphore:
            return await fetch_video_page(mid, session, page_num, page_size, delay_seconds)
    
    # 从第二页开始创建任务
    tasks = [fetch_page_with_semaphore(page) for page in range(2, total_pages + 1)]

    try:
        # 使用tqdm来显示进度
        remaining_pages = []
        pbar = tqdm_asyncio(total=len(tasks), desc=f"获取用户 {mid} 视频列表", leave=False)
        for f in asyncio.as_completed(tasks):
            page_result = await f
            if isinstance(page_result, dict):
                remaining_pages.append(page_result)
            pbar.update(1)
        pbar.close()
    except Exception as e:
        logger.error(f"获取用户 {mid} 视频列表时发生错误: {str(e)}")
        return []
    
    # 合并所有视频
    for page in remaining_pages:
        videos_in_page = page.get('videos', [])

        # 确保 videos_in_page 是列表
        if isinstance(videos_in_page, list):
            all_videos.extend(videos_in_page)
        else:
            logger.warning(f"用户 {mid} 的某个分页返回了无效的 'videos' 字段, 已跳过. 数据: {videos_in_page}")
    
    return all_videos

async def fetch_batch_data(
        videos: List[Video],
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        url: str,
        process_func: Callable[[Dict[str, Any]], Any],
        *,
        delay_seconds: Callable[[], float] = DELAY_SECONDS,
        retry_times: int = None,
        retry_delay: int = None
) -> Dict[str, Any]:
    """批量批量数据获取函数

    Args:
        videos (List[Video]): 要获取数据的视频列表
        session (aiohttp.ClientSession): aiohttp会话
        url (str): API地址
        process_func (Callable[[Dict[str, Any]], Any]): 数据处理函数
        max_concurrent (int, optional): 最大并发请求数. Defaults to None.
        delay_seconds (Callable[[], float], optional): 请求延迟函数. Defaults to DELAY_SECONDS.
        retry_times (int, optional): 批次重试次数. Defaults to None.
        retry_delay (int, optional): 批次重试延迟. Defaults to None.

    Returns:
        Dict[str, Any]: 以视频bvid为键的数据字典
    """

    config = BATCH_FETCH_CONFIG.copy()
    if retry_times is not None:
        config['retry_times'] = retry_times
    if retry_delay is not None:
        config['retry_delay'] = retry_delay

    api_semaphore = semaphore
    result_dict = {}
    failed_videos = videos

    for attempt in range(config['retry_times'] + 1):
        if not failed_videos:
            break

        if attempt > 0:
            logger.warning(f"第 {attempt} 次重试获取 {len(failed_videos)} 个视频的数据")
            await asyncio.sleep(config['retry_delay'] * attempt)

        async def fetch_with_semaphore(video: Video) -> Tuple[str, Any, bool]:
            async with api_semaphore:
                try:
                    params = {'bvid': video.bvid}

                    data = await make_api_request(
                        url=url,
                        params=params,
                        need_wbi=False,
                        process_data=process_func,
                        session=session,
                        delay_seconds=delay_seconds,
                    )
                    return video.bvid, data, True
                except Exception as e:
                    logger.error(f"获取视频 {video.bvid} 数据失败: {str(e)}")
                    return video.bvid, None, False
                
        # 创建当前批次的请求任务
        tasks = [fetch_with_semaphore(video) for video in failed_videos]

        # 并发执行请求
        try:
            current_result = await asyncio.gather(*tasks, return_exceptions=False)

            # 更新结果并收集失败的视频
            next_failed_videos = []
            for bvid, data, success in current_result:
                if success:
                    result_dict[bvid] = data
                else:
                    next_video = next(v for v in failed_videos if v.bvid == bvid)
                    next_failed_videos.append(next_video)
            
            failed_videos = next_failed_videos

            if failed_videos:
                logger.warning(f"本批次仍有 {len(failed_videos)} 个视频获取数据失败")

        except Exception as e:
            logger.error(f"批量获取数据时发生错误: {str(e)}")
            continue
    
    if failed_videos:
        logger.error(f"最终仍有 {len(failed_videos)} 个视频的数据获取失败")
        # 为失败的视频添加空数据
        for video in failed_videos:
            result_dict[video.bvid] = []

    return result_dict

async def fetch_parts(videos: List[Video], session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, **kwargs) -> Dict[str, List[VideoPart]]:
    """批量获取视频分P信息"""
    def process_parts(data: Dict[str, Any]) -> List[VideoPart]:
        try:
            return list(map(VideoPart, data['data']))
        except Exception as e:
            raise Exception(f"分P数据解析失败: {e}")
        
    return await fetch_batch_data(
        videos=videos,
        session=session,
        semaphore=semaphore,
        url="https://api.bilibili.com/x/player/pagelist",
        process_func=process_parts,
        **kwargs
    )
    
async def fetch_tags(videos: List[Video], session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, **kwargs) -> Dict[str, List[str]]:
    """批量获取视频标签"""
    def process_tags(data: Dict[str, Any]) -> List[str]:
        return list(map(lambda tag: tag['tag_name'], data.get('data', [])))
    
    return await fetch_batch_data(
        videos=videos,
        session=session,
        semaphore=semaphore,
        url="https://api.bilibili.com/x/web-interface/view/detail/tag",
        process_func=process_tags,
        **kwargs
    )


if __name__ == "__main__":
    async def test():
        test_semaphore = asyncio.Semaphore(5)
        # 测试 fetch_video_list
        if True:
            mid = 66508
            async with aiohttp.ClientSession() as session:
                video_list = await fetch_video_list(mid, session)
                print(f"Total videos fetched: {len(video_list)}")
                
        # 测试 fetch_parts
        if True:
            bvid = "BV1Gx411w7wU"
            # 创建一个Video对象用于测试
            video = Video({'aid': 1, 'bvid': bvid, 'mid': 1, 'title': 'test', 'description': 'test', 'pic': 'test', 'created': 1234567890})
            async with aiohttp.ClientSession() as session:
                parts_dict = await fetch_parts([video], session, test_semaphore)
                print(f"Total parts fetched: {len(parts_dict.get(bvid, []))}")
            
        # 测试 fetch_tags
        if True:
            bvid = "BV1Gx411w7wU"
            video = Video({'aid': 1, 'bvid': bvid, 'mid': 1, 'title': 'test', 'description': 'test', 'pic': 'test', 'created': 1234567890})
            async with aiohttp.ClientSession() as session:
                tags_dict = await fetch_tags([video], session, test_semaphore)
                print(f"Tags: {tags_dict.get(bvid, [])}")
    # 运行测试
    asyncio.run(test())
import asyncio
import aiohttp
import logging
from typing import Callable, TypeVar, Dict, Any

from config import HEADERS, DELAY_SECONDS
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


async def fetch_video_list(mid: int, session: aiohttp.ClientSession, page_size: int = 50, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[Video]:
    """获取用户所有视频列表（使用循环代替递归）"""
    all_videos = []
    page_number = 1
    total_pages = 1  # 初始化为1，第一次请求后更新
    
    while page_number <= total_pages:
        params = {
            'mid': mid,
            'pn': page_number,
            'ps': page_size
        }
        
        def process_video_lists(data: Dict[str, Any]) -> list[Video]:
            nonlocal total_pages
            vlist = data['data']['list']['vlist']
            total_videos = data['data']['page']['count']
            total_pages = (total_videos + page_size - 1) // page_size
            
            page_videos = []
            for item in vlist:
                try:
                    page_videos.append(Video(item))
                except Exception as e:
                    logger.warning(f"视频 {item.get('bvid')} 数据解析错误: {e}")
            return page_videos
        
        try:
            page_videos = await make_api_request(
                url="https://api.bilibili.com/x/space/wbi/arc/search",
                params=params,
                need_wbi=True,
                process_data=process_video_lists,
                session=session,
                delay_seconds=delay_seconds,
            )
            all_videos.extend(page_videos)
            logger.info(f"已获取用户 {mid} 第 {page_number}/{total_pages} 页视频")
        except Exception as e:
            logger.error(f"获取用户 {mid} 第 {page_number} 页视频失败: {str(e)}")
            # 跳过当前页继续下一页
            if page_number >= total_pages:
                break
        
        page_number += 1
    
    return all_videos


async def fetch_video_parts(bvid: str, session: aiohttp.ClientSession, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[VideoPart]:
    params = {
        'bvid': bvid
    }
    
    def process_video_parts(data: Dict[str, Any]) -> list[VideoPart]:
        try:
            return list(map(VideoPart, data['data']))
        except Exception as e:
            raise Exception(f"分P数据解析错误: {e}")
    
    return await make_api_request(
        url="https://api.bilibili.com/x/player/pagelist",
        params=params,
        need_wbi=False,
        process_data=process_video_parts,
        session=session,
        delay_seconds=delay_seconds,
    )


async def fetch_video_tags(bvid: str, session: aiohttp.ClientSession, delay_seconds: Callable[[], float] = DELAY_SECONDS) -> list[str]:
    params = {
        'bvid': bvid
    }
    
    def process_video_tags(data: Dict[str, Any]) -> list[str]:
        return list(map(lambda tag: tag['tag_name'], data.get('data', [])))
    
    return await make_api_request(
        url="https://api.bilibili.com/x/web-interface/view/detail/tag",
        params=params,
        need_wbi=False,
        process_data=process_video_tags,
        session=session,
        delay_seconds=delay_seconds,
    )

if __name__ == "__main__":
    if True: # test fetch_video_list
        mid = 66508
        video_list = fetch_video_list(mid)
        print(f"Total videos fetched: {len(video_list)}")


    if True: # test fetch_video_parts
        bvid = "BV1Gx411w7wU"
        plist = fetch_video_parts(bvid)
        print(f"Total parts fetched: {len(plist)}")

    if True: # test fetch_video_tags
        bvid = "BV1Gx411w7wU"
        tags = fetch_video_tags(bvid)
        print(f"Tags: {tags}")
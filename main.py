from functools import reduce
from hashlib import md5
import urllib.parse
import time
import requests
import csv
import os
from dotenv import load_dotenv


class WbiSigner:
    """WBI 签名类，用于对 B 站 API 请求参数进行签名 (来源BAC)"""
    mixin_key_enc_tab = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]

    @staticmethod
    def get_mixin_key(orig: str):
        """对 imgKey 和 subKey 进行字符顺序打乱编码"""
        return reduce(lambda s, i: s + orig[i], WbiSigner.mixin_key_enc_tab, '')[:32]

    @staticmethod
    def enc_wbi(params: dict, img_key: str, sub_key: str):
        """为请求参数进行 wbi 签名"""
        mixin_key = WbiSigner.get_mixin_key(img_key + sub_key)
        curr_time = round(time.time())
        params['wts'] = curr_time                                   # 添加 wts 字段
        params = dict(sorted(params.items()))                       # 按照 key 重排参数
        # 过滤 value 中的 "!'()*" 字符
        params = {
            k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
            for k, v 
            in params.items()
        }
        query = urllib.parse.urlencode(params)                      # 序列化参数
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()    # 计算 w_rid
        params['w_rid'] = wbi_sign
        return params

    @staticmethod
    def get_wbi_keys() -> tuple[str, str]:
        """获取最新的 img_key 和 sub_key"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'Referer': 'https://www.bilibili.com/'
        }
        resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers)
        resp.raise_for_status()
        json_content = resp.json()
        img_url: str = json_content['data']['wbi_img']['img_url']
        sub_url: str = json_content['data']['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key


class BiliUPVideoInfoFetcher:
    """B站指定UP主视频信息获取类"""
    def __init__(self, mid: str):
        self.mid = mid  
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'Cookie': f"SESSDATA={os.getenv('SESSDATA')}"  # 从环境变量获取 SESSDATA
        }

    def get_cid_by_bvid(self, bvid: str) -> list[dict]:
        """通过bvid获取视频所有分P的cid信息"""
        params = {'bvid': bvid}
        try:
            response = requests.get(
                url="https://api.bilibili.com/x/player/pagelist",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get('code') != 0:
                print(f"API错误: {data.get('code')}, 错误信息: {data.get('message')}")
                return []

            return data.get('data', [])
        except requests.RequestException as e:
            print(f"获取分P信息失败: {e}")
            return []

    def fetch_all_videos(self) -> list[dict]:
        """获取目标UP主的所有视频信息"""
        img_key, sub_key = WbiSigner.get_wbi_keys()  # 获取 WBI 签名秘钥

        all_videos = []
        page = 1
        page_size = 50  # 每页视频数量

        while True:
            params = {
                'mid': self.mid,
                'pn': page,
                'ps': page_size
            }

            # 添加 WBI 签名
            signed_params = WbiSigner.enc_wbi(params, img_key, sub_key)

            try:
                response = requests.get(
                    url="https://api.bilibili.com/x/space/wbi/arc/search",
                    headers=self.headers,
                    params=signed_params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                # 检查返回状态
                if data.get('code') != 0:
                    print(f"API错误: {data.get('code')}, 错误信息: {data.get('message')}")
                    break

                # 检查数据结构
                if 'data' not in data or 'list' not in data['data'] or 'vlist' not in data['data']['list']:
                    break  
                
                # 获取分页信息 计算总页数
                page_info = data['data']['page']
                total_pages = (page_info['count'] + page_size - 1) // page_size  

                videos = data['data']['list']['vlist']
                if not videos:
                    break  

                # 获取每个视频的详细信息
                for video in videos:
                    parts = self.get_cid_by_bvid(video['bvid'])
                    video['parts'] = parts # 添加分P信息到视频数据
                    time.sleep(0.5)  # 避免请求过快

                all_videos.extend(videos)
                
                # 分页控制
                if page >= total_pages:
                    break  # 如果已经是最后一页，则退出循环

                page += 1  # 翻页
                time.sleep(1)  # 避免请求过快

            except requests.RequestException as e:
                print(f"请求失败: {e}")
                break

        return all_videos
    
    def save_to_csv(self, videos: list[dict], filename: str):
        """将视频信息保存到 CSV 文件"""
        if not videos:
            print("没有视频数据可保存")
            return
        
        # 需要保存的字段
        fields = ['title', 'aid', 'bvid', 'cid', 'parts_count', 'created', 'play', 
                  'video_review', 'comment', 'length', 'pic', 'description']

        try:
            with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                
                for video in videos:
                    # 时间戳转换
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(video['created']))

                    # 获取分P信息与其对应的CID
                    parts = video.get('parts', [])
                    parts_count = len(parts)
                    all_cids = [str(part['cid']) for part in parts]

                    row = {
                        'title': video.get('title', ''),
                        'aid': video.get('aid', ''),
                        'bvid': video.get('bvid', ''),
                        'cid': '; '.join(all_cids),  # 分P的CID合并为字符串
                        'parts_count': parts_count,
                        'created': created_time,
                        'play': video.get('play', ''),
                        'video_review': video.get('video_review', ''),
                        'comment': video.get('comment', ''),
                        'length': video.get('length', ''),
                        'pic': video.get('pic', ''),
                        'description': video.get('description', '')
                    }
                    writer.writerow(row)
            print(f"成功保存 {len(videos)} 条视频信息到 {filename}")
        except IOError as e:
            print(f"保存到CSV失败: {e}")

    def fetch_and_save(self, filename: str):
        """获取视频信息并保存到 CSV 文件"""
        videos = self.fetch_all_videos()
        self.save_to_csv(videos, filename)
        

if __name__ == "__main__":
    load_dotenv(".env")  # 加载环境变量
    UID = ""  # 目标UP主的UID
    fetcher = BiliUPVideoInfoFetcher(mid=UID)  # 创建 BiliUPVideoInfoFetcher 实例
    fetcher.fetch_and_save(f'{UID}_all_videos.csv')  # 获取视频信息并保存到 CSV 文件
    
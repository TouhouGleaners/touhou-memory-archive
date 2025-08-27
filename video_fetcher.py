import time
import requests
import csv
from wbi_signer import WbiSigner


class BiliUPVideoInfoFetcher:
    """B站指定UP主视频信息获取类"""
    def __init__(self, mid: str, sessdata: str):
        if not sessdata or not sessdata.strip():
            raise ValueError("SESSDATA是必需的参数，不能为空")
        
        self.mid = mid
        self.sessdata = sessdata  
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'Cookie': f"SESSDATA={sessdata}"  
        }

    def get_cid_by_bvid(self, bvid: str) -> list[dict]:
        """通过bvid获取视频所有分P的cid信息"""
        params = {'bvid': bvid}
        try:
            response = requests.get(
                url="https://api.bilibili.com/x/player/pagelist",
                headers=self.headers,
                params=params,
                timeout=5
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
                    timeout=5
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
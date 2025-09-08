class Video:
    def __init__(self, data: dict):
        self.aid = data['aid']
        self.bvid = data['bvid']
        self.mid = data['mid']
        self.title = data['title']
        self.description = data['description']
        self.pic = data['pic']
        self.created = data['created']
        self.tags = []

class VideoPart:
    def __init__(self, data: dict):
        self.cid = data['cid']
        self.page = data['page']
        self.part = data['part']
        self.duration = data['duration']
        self.ctime = data['ctime']
import requests, time
import urllib

class CG:
    def __init__(self, phone, token, org):
        self.HEADER = {
            'Host': 'kt.educg.net',
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Linux; Android 14; 24031PN0DC Build/UKQ1.231003.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160083 MMWEBSDK/20231201 MMWEBID/7416 MicroMessenger/8.0.45.2521(0x28002D34) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64 miniProgram/wx7dc0e08387a8e188',
            'x-requested-with': 'com.tencent.mm',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://kt.educg.net/cgWeb/index.html',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        self.phone = phone
        self.token = token
        self.org = org

        self.userInfo = self.get_user_query()['data'][0]
        self.sid = self.userInfo['student']['id']

    def get_user_query(self):
        params = {
            'token': self.token,
            'phone': self.phone,
            'org': self.org,
            'ts': str(int(time.time()*1000)),
        }

        response = requests.get('https://kt.educg.net/user/query', params=params, headers=self.HEADER)

        return response.json()

    def query_checkin(self, checkinId):
        params = {
            'id': checkinId
        }

        response = requests.get('https://kt.educg.net/query/checkin', params=params, headers={
            'sid': self.sid,
            'ts': str(int(time.time()*1000)),
            'org': self.org,
            'token': self.token,
            **self.HEADER
        })

        return response.json()

    def do_checkin(self, checkinId, loc):
        params = {
            'location': loc,
            'id': checkinId
        }

        response = requests.post('https://kt.educg.net/checkin/do', data=urllib.parse.urlencode(params), headers={
            'sid': self.sid,
            'ts': str(int(time.time()*1000)),
            'org': self.org,
            'token': self.token,
            'content-type': 'application/x-www-form-urlencoded',
            **self.HEADER
        })

        return response.text

import requests
import base64
import time
import os
import json
import re
import datetime

from logger import logger

from Crypto.Cipher import AES

signTmp = []

class ChaoXing:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.session()
        self.useragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 com.ssreader.ChaoXingStudy/ChaoXingStudy_3_4.8_ios_phone_202012052220_56 (@Kalimdor)_12787186548451577248'

    def pad(self, text):
        """ 对需要加密的明文进行填充补位
        @param text: 需要进行填充补位操作的明文
        @return: 补齐明文字符串
        """
        block_size = 16

        text_length = len(text)
        # 计算需要填充的位数
        amount_to_pad = block_size - (text_length % block_size)
        if amount_to_pad == 0:
            amount_to_pad = block_size
        # 获得补位所用的字符
        pad = chr(amount_to_pad).encode()
        return text + pad * amount_to_pad

    def encrypt(self, text):
        AES_KEY = "u2oh6Vu^HWe4_AES"
        ciper = AES.new(AES_KEY.encode(), AES.MODE_CBC, AES_KEY.encode())
        # logger.debug(base64.b64encode(ciper.encrypt(self.pad(text.encode()))).decode())
        return base64.b64encode(ciper.encrypt(self.pad(text.encode()))).decode()

    def login(self):
        # 查看本地是否已保存过
        if os.path.exists("cookies.json"):
            self.cookies = json.loads(open("cookies.json").read())
            tokenTime = time.time()-int(self.cookies['_d'])/1000
            logger.info(f"cookie 已使用 {tokenTime/60/60} 小时")
            if tokenTime < 2*24*60*60: # token在48小时内生成
                self.session.cookies.update(self.cookies)
                return

        logger.info("刷新 cookie")
        url = 'https://passport2.chaoxing.com/fanyalogin'
        headers = {
            'User-Agent': self.useragent,
            'Referer': r'http://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Fi.chaoxing.com'
        }
        data = {
            'fid': -1,
            'uname': self.encrypt(self.username),
            'password': self.encrypt(self.password),
            'refer': r'https%253A%252F%252Fi.chaoxing.com',
            't': True,
            'forbidotherlogin': 0
        }
        # 发送请求
        res = self.session.post(url, headers=headers, data=data)

        self.cookies = res.cookies.get_dict()
        # 保存到本地
        with open("cookies.json", "w+") as f:
            f.write(json.dumps(self.cookies, ensure_ascii=False))

    def get_im(self):
        url = 'https://im.chaoxing.com/webim/me'
        headers = {
            'User-Agent': self.useragent
        }
        # 发送请求
        res = self.session.get(url, headers=headers)

        return re.search(r"loginByToken\('(\d+?)', '([^']+?)'\);", res.text).groups()

    def get_course(self):
        url = 'https://mooc1-api.chaoxing.com/mycourse/backclazzdata'
        headers = {
            'User-Agent': self.useragent
        }
        # 发送请求
        res = self.session.get(url, headers=headers)

        return res.json()

    def allCourse(self):
        course = self.get_course()
        chatIdList = []
        for i in course['channelList']:
            if 'course' in i['content']:
                logger.info(f"{i['content']['course']['data'][0]['name']} courseid: {i['content']['course']['data'][0]['id']} classid: {i['content']['id']}")
                chatIdList.append(i['content']['chatid'])

        im = cx.get_im()
        chatList = json.loads(re.search(r"var classChat=(.*?);\r\n", im).group(1))
        for i in chatList:
            if i.replace("chatid", "") not in chatIdList:
                logger.info(f"{i} {chatList[i]}")

    def get_active(self, courseId, classId):
        url = 'https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist'
        headers = {
            'User-Agent': self.useragent
        }
        params = {
            'courseId': courseId,
            'classId': classId,
            'uid': self.cookies['UID']
        }
        # 发送请求
        res = self.session.get(url, headers=headers, params=params)
        return res.json()

    def get_active_new(self, courseId, classId):
        url = 'https://mobilelearn.chaoxing.com/v2/apis/active/student/activelist'
        headers = {
            'User-Agent': self.useragent
        }
        params = {
            'courseId': courseId,
            'classId': classId,
            'fid': 0
        }
        # 发送请求
        res = self.session.get(url, headers=headers, params=params)
        return res.json()

    def get_PPT_active_info(self, activeId):
        url = 'https://mobilelearn.chaoxing.com/v2/apis/active/getPPTActiveInfo'
        headers = {
            'User-Agent': self.useragent
        }
        params = {
            'activeId': activeId,
            'duid': '',
            'denc': ''
        }
        # 发送请求
        res = self.session.get(url, headers=headers, params=params)
        return res.json()

    def getSignType(item):
        if item['otherId'] == 0:
            if item['ifphoto'] == 1:
                return '拍照签到'
            else:
                return '普通签到'
        elif item['otherId'] == 2:
            return '二维码签到'
        elif item['otherId'] == 3:
            return '手势签到'
        elif item['otherId'] == 4:
            return '位置签到'
        elif item['otherId'] == 5:
            return '签到码签到'
        else:
            return '未知'

    def getAccountInfo(self):
        url = 'http://passport2.chaoxing.com/mooc/accountManage'
        headers = {
            'User-Agent': self.useragent
        }
        # 发送请求
        res = self.session.get(url, headers=headers)
        return res.text

    def addResult(self, item, result, status):
        try:
            result.append(f"{datetime.datetime.fromtimestamp(item['startTime']/1000).strftime('%m-%d %H:%M:%S')} 至 {datetime.datetime.fromtimestamp(item['endTime']/1000).strftime('%m-%d %H:%M:%S')}")
            result.append(status)
            result.append("")
        except:
            result.append(f"{item['id']} {status}")

    def SignByCourse(self, courseId, classId, pos):
        result = [f"课程 {courseId}-{classId}"]

        self.name = re.search(r" (\S*?)\r\n(\s*?)</p>姓名\r\n", self.getAccountInfo()).group(1)

        activeList = self.get_active_new(courseId, classId)['data']['activeList']

        headers = {
            'User-Agent': self.useragent
        }

        for item in activeList:
            # logger.info(item)
            if item['activeType'] == 2 and int(item['otherId']) >= 0 and int(item['otherId']) <= 5 and item['status'] == 1 and item['id'] not in signTmp:
                # preSign
                url = f"https://mobilelearn.chaoxing.com/newsign/preSign?courseId={courseId}&classId={classId}&activePrimaryId={item['id']}&general=1&sys=1&ls=1&appType=15&&tid=&uid={self.cookies['UID']}&ut=s"
                res = self.session.get(url, headers=headers)
                logger.debug(f"preSign {res.status_code}")
                preSign = res.text

                url = f"https://mobilelearn.chaoxing.com/pptSign/analysis?vs=1&DB_STRATEGY=RANDOM&aid={item['id']}"
                res = self.session.get(url, headers=headers)
                logger.debug(f"analysis {res.text}")

                code = re.search("code='\+'(.*)'", res.text).group(1)
                url = f"https://mobilelearn.chaoxing.com/pptSign/analysis2?DB_STRATEGY=RANDOM&code={code}"
                res = self.session.get(url, headers=headers)
                logger.debug("analysis2 {res.text}")

                if int(item['otherId']) == 0: # 普通签到 / 拍照签到
                    if "拍照" in preSign:
                        logger.warning("拍照签到暂不支持")
                        signTmp.append(item['id'])
                        self.addResult(item, result, "拍照签到 不支持")

                    else: # 普通签到
                        url = f"https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId={item['id']}&uid={self.cookies['UID']}&clientip=&latitude=-1&longitude=-1&appType=15&fid={self.cookies['fid']}&name={self.name}"
                        logger.debug(url)
                        res = self.session.get(url, headers=headers)
                        logger.info(f"stuSignajax {res.text}")
                        if res.text == "success" or res.text == "您已签到过了":
                            signTmp.append(item['id'])
                            self.addResult(item, result, "普通签到 已签到")
                        else:
                            self.addResult(item, result, "普通签到 签到失败")

                elif int(item['otherId']) == 2: # 扫一扫签到
                    logger.warning("扫一扫签到暂不支持")
                    signTmp.append(item['id'])
                    result.append(f"{item['id']} 扫一扫签到 不支持")

                elif int(item['otherId']) == 3: # 手势签到
                    url = f"https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId={item['id']}&uid={self.cookies['UID']}&clientip=&latitude=-1&longitude=-1&appType=15&fid={self.cookies['fid']}&name={self.name}"
                    res = self.session.get(url, headers=headers)
                    logger.info(f"stuSignajax {res.text}")
                    if res.text == "success" or res.text == "您已签到过了":
                        signTmp.append(item['id'])
                        self.addResult(item, result, "手势签到 已签到")
                    else:
                        self.addResult(item, result, "手势签到 签到失败")
                        if '90002' in res.text:
                            signTmp.append(item['id'])

                elif int(item['otherId']) == 5: # 签到码签到
                    url = f"https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId={item['id']}&uid={self.cookies['UID']}&clientip=&latitude=-1&longitude=-1&appType=15&fid={self.cookies['fid']}&name={self.name}"
                    res = self.session.get(url, headers=headers)
                    logger.info(f"stuSignajax {res.text}")
                    if res.text == "success" or res.text == "您已签到过了":
                        signTmp.append(item['id'])
                        self.addResult(item, result, "签到码签到 已签到")
                    else:
                        self.addResult(item, result, "签到码签到 签到失败")
                        if '90002' in res.text:
                            signTmp.append(item['id'])

                elif int(item['otherId']) == 4: # 位置签到
                    try:
                        ifopenAddress = re.findall(r'<input type="hidden" id="ifopenAddress" value="(.*?)">', preSign)[0]
                        locationText = re.findall(r'<input type="hidden" id="locationText" value="(.*?)">', preSign)[0]
                        locationLatitude = re.findall(r'<input type="hidden" id="locationLatitude" value="(.*?)">', preSign)[0]
                        locationLongitude = re.findall(r'<input type="hidden" id="locationLongitude" value="(.*?)">', preSign)[0]
                        locationRange = re.findall(r'<input type="hidden" id="locationRange" value="(.*?)">', preSign)[0]

                        logger.debug(f"IfopenAddress: {ifopenAddress}")
                        logger.debug(f"LocationText: {locationText}")
                        logger.debug(f"LocationLatitude: {locationLatitude}")
                        logger.debug(f"LocationLongitude: {locationLongitude}")
                        logger.debug(f"LocationRange: {locationRange}")

                    except:
                        pass

                    url = f"https://mobilelearn.chaoxing.com/pptSign/stuSignajax?name={self.name}&address={pos['address']}&activeId={item['id']}&uid={self.cookies['UID']}&clientip=&latitude={pos['lat']}&longitude={pos['lon']}&fid={self.cookies['fid']}&appType=15&ifTiJiao=1"
                    res = self.session.get(url, headers=headers)
                    logger.info(f"stuSignajax {res.text}")
                    if res.text == "success" or res.text == "您已签到过了":
                        signTmp.append(item['id'])
                        self.addResult(item, result, "位置签到 已签到")
                    else:
                        self.addResult(item, result, "位置签到 签到失败")

        return result

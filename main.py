from chaoxing import ChaoXing
from im import get_wsurl, build_login_msg, get_chat_id, build_release_session_msg, get_attachment
from course import getNowLesson, getNextLesson, getRecentLesson
from push import pushNotice
from logger import logger

import asyncio, threading
import websockets
import base64, json
import time, datetime
import traceback


CONFIG = {
    "account": "超星手机号",
    "password": "超星密码",
    "termStartDate": "2024-02-26", #学期开始日
    "courseJson": "course_2024春.json",
    "sectionJson": "section_冬季作息.json"
}

posList = json.loads(open("signpos.json").read())
signinfoList = json.loads(open("signinfo_2024春.json").read())

heart_ts = time.time()

async def cx_main():
    global heart_ts

    cx = ChaoXing(CONFIG['account'], CONFIG['password'])
    cx.login()

    uid, imToken = cx.get_im()

    async with websockets.connect(get_wsurl(), ping_interval=None) as websocket:
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60)
            except asyncio.TimeoutError: # 心跳超时
                logger.error("ws心跳/响应超时，可能是网络断开，重新连接")
                break

            logger.debug(f"Received(raw): {response}")

            if response[0] == "h": # 收到心跳
                heart_ts = time.time() # 需要重置心跳超时计时

            elif response[0] == "o": # 收到登录请求
                message = build_login_msg(uid, imToken)
                logger.debug(f"Sent(raw): {message}")
                message = json.dumps([base64.b64encode(message).decode()])
                logger.debug(f"Sent(enc): {message}")
                await websocket.send(message)

                logger.info("登录成功，开始查找最近课程签到")
                # 每次登录后查找前后一小时的课程+？？，获取列表尝试进行签到
                recentLessonList = getRecentLesson(CONFIG['termStartDate'], CONFIG['courseJson'], CONFIG['sectionJson'])
                for l in recentLessonList:
                    if l in signinfoList and signinfoList[l]['signmode'] == 1:
                        logger.info(f"正在查找 {l}")
                        cx.SignByCourse(
                            signinfoList[l]['courseid'],
                            signinfoList[l]['classid'],
                            posList[signinfoList[l]['signpos']]
                        )
                        logger.info(f"正在查找 ？？")
                        cx.SignByCourse( # 特殊的？？ 需要修改
                            xxxxxx,
                            xxxxxx,
                            posList[signinfoList[l]['signpos']]
                        )


            elif response[0] == "a":
                response = json.loads(response[1:])

                for i in response:
                    msg = base64.b64decode(i)
                    logger.debug(f"Received(dec): {msg}")

                    if len(msg) <= 5:
                        continue

                    if msg[0:5] == bytes([0x08, 0x00, 0x40, 0x03, 0x4a]):
                        clientID = msg[14:].decode()
                        logger.info(f"IM 接收到登录成功, clientID: {clientID}")

                    if msg[0:5] == bytes([0x08, 0x00, 0x40, 0x02, 0x4a]): # MsgHeaderCourse
                        msgLength = int(msg[9])
                        if msgLength > 0:
                            chatID = msg[10:10+msgLength].decode()
                            logger.info(f"IM 接收到课程消息, chatID: {chatID}")

                            message = bytearray(msg)
                            message.extend(bytes([0x58, 0x00]))
                            message[3] = 0x00
                            message[6] = 0x1a

                            logger.debug(f"Sent(raw): {message}")
                            message = json.dumps([base64.b64encode(message).decode()])
                            logger.debug(f"Sent(enc): {message}")
                            await websocket.send(message)

                    elif msg[0:5] == bytes([0x08, 0x00, 0x40, 0x00, 0x4a]): # MsgHeaderActive
                        chatID = get_chat_id(msg)
                        if not chatID:
                            logger.info("解析出错 chatID == None")
                            continue

                        logger.info(f"IM 接收到活动信息, chatID: {chatID}")

                        sessionEnd = 11 # 第一个消息的开头位置

                        while True:
                            index = sessionEnd

                            if msg[index] != 0x22: # 解析完毕
                                break
                            index += 1

                            sessionEnd = index + 2+ msg[index] + (msg[index+1]-1)*0x80 # 下一个消息的开头位置
                            index += 2

                            if msg[index] != 0x08:
                                logger.warning("解析出错 msg[index] != 0x08")
                                break
                            index += 1

                            logger.debug("释放 Session")
                            message = build_release_session_msg(chatID, msg[index:index+9])
                            index += 9

                            logger.debug(f"Sent(raw): {message}")
                            message = json.dumps([base64.b64encode(message).decode()])
                            logger.debug(f"Sent(enc): {message}")
                            await websocket.send(message)

                            logger.debug(f"消息原始内容: {msg[index:sessionEnd]}")

                            attachment = get_attachment(msg, index, sessionEnd)

                            logger.debug(f"解析 attachment: {attachment}")
                            if not attachment:
                                continue

                            with open(f"attachment/{int(time.time()*1000)}.json", "w+") as f:
                                f.write(json.dumps(attachment, ensure_ascii=False, separators=(',',':')))

                            if attachment['attachmentType'] == 15: # 活动


                                if attachment['att_chat_course']['atype'] == 0 or attachment['att_chat_course']['atype'] == 2: # 签到活动
                                    logger.info("收到 签到 活动")
                                else:
                                    logger.info(f"收到 {attachment['att_chat_course']['atypeName'] if 'atypeName' in attachment['att_chat_course'] else '未知'} 活动")
                                    continue

                                signinfo = None

                                for c in signinfoList:
                                    if (attachment['att_chat_course']['courseInfo']['courseid'] == signinfoList[c]['courseid']) and (attachment['att_chat_course']['courseInfo']['classid'] == signinfoList[c]['classid']):
                                        logger.info(f"匹配到课程 {c}")
                                        signinfo = signinfo[c]

                                if not signinfo:
                                    nextLesson = getNextLesson(CONFIG['termStartDate'], CONFIG['courseJson'], CONFIG['sectionJson'])
                                    logger.info(f"自动推断下节课是 {nextLesson}")
                                    signinfo = signinfoList[nextLesson['name']]

                                logger.info(f"签到信息 {signinfo}")

                                result = cx.SignByCourse(
                                    attachment['att_chat_course']['courseInfo']['courseid'],
                                    attachment['att_chat_course']['courseInfo']['classid'],
                                    posList[signinfo['signpos']]
                                )
                                if len(result) > 1:
                                    if 'coursename' in attachment['att_chat_course']['courseInfo']:
                                        result[0] = f"课程 {attachment['att_chat_course']['courseInfo']['coursename']}"
                                    tmp = pushNotice("\n".join(result))
                                    logger.info(f"推送签到结果 {tmp}")

def task_cx():
    while True:
        try:
            asyncio.run(cx_main())
        except Exception as e:
            traceback.print_exc()

            logger.error(f"超星线程 遇到错误 {e} 5s后重新启动")
            try:
                pushNotice(f"超星线程 遇到错误 {e} 5s后重新启动")
            except:
                logger.error("超星线程 网络断开，等待30s")
                time.sleep(30)

            time.sleep(5)


# cg部分
from cg import CG

def task_cg():
    cg = CG('希冀手机号', '希冀小程序token', '希冀小程序orgid') # 需要手动抓包配置

    cgSignTmp = []

    while True:
        try:
            cg_run = False
            now = datetime.datetime.now()-datetime.timedelta(minutes=10)

            for i in range(3):
                nowCourse = getNowLesson(now.strftime("%Y-%m-%d %H:%M"), CONFIG['termStartDate'], CONFIG['courseJson'], CONFIG['sectionJson'])
                if nowCourse and 'xxxx' in nowCourse['name']:
                    cg_run = True
                    break
                now += datetime.timedelta(minutes=10)

            if cg_run:
                logger.debug(f"希冀轮询")
                cg.userInfo = cg.get_user_query()['data'][0]
                for course in cg.userInfo['active']:
                    for check in course['checkin']:
                        if check['id'] not in cgSignTmp:
                            logger.info(f"希冀签到 {check['id']}")
                            cg.do_checkin(check['id'], "36.xxxx、117.xxxx") # 需要手动配置/抓包

                            query = cg.query_checkin(check['id'])

                            result = f"课程 xxxx（希冀）\n{datetime.datetime.fromtimestamp(query['data']['detail']['start']/1000).strftime('%m-%d %H:%M:%S')} 至 {datetime.datetime.fromtimestamp(query['data']['detail']['end']/1000).strftime('%m-%d %H:%M:%S')}\n"

                            if list(query['data']['history']) > 0:
                                cgSignTmp.append(check['id'])
                                logger.info(f"希冀签到成功")
                                result += "签到成功\n"
                            else:
                                logger.warning(f"希冀签到失败")
                                result += "签到失败\n"

                            tmp = pushNotice(result)
                            logger.info(f"推送签到结果 {tmp}")

            time.sleep(60)
        except Exception as e:
            traceback.print_exc()

            logger.error(f"希冀线程 遇到错误 {e} 5s后重新启动")
            try:
                pushNotice(f"希冀线程 遇到错误 {e} 5s后重新启动")
            except:
                logger.error("希冀线程 网络断开，等待30s")
                time.sleep(30)

            time.sleep(5)


if __name__ == "__main__":
    th_cx = threading.Thread(target=task_cx)
    th_cx.start()

    th_cg = threading.Thread(target=task_cg)
    th_cg.start()

    th_cx.join()
    th_cg.join()

import datetime, json

def getNowLesson(nowTime_str, termStartDate_str, courseJson_name, sectionJson_name):
    nowTime = datetime.datetime.strptime(nowTime_str, "%Y-%m-%d %H:%M")
    termStartDate = datetime.datetime.strptime(termStartDate_str, "%Y-%m-%d")

    courseJson = json.loads(open(courseJson_name).read())
    sectionJson = json.loads(open(sectionJson_name).read())

    # 计算当前周数
    nowWeek = (nowTime-termStartDate).days//7+1

    nowCourse = None

    for i in courseJson:
        # 筛选本周课程
        if nowWeek not in i['weeks']:
            continue

        # 筛选当天课程
        if nowTime.weekday()+1 != i['day']:
            continue

        # 计算上课和下课时间
        courseStart, courseEnd = sectionJson[i['sections'][0]-1].split('-')[0], sectionJson[i['sections'][-1]-1].split('-')[1]

        # 判断当前时间是否在此课程范围内
        if int(courseStart.replace(':',"")) <= int(nowTime_str.split(' ')[1].replace(':',"")) <= int(courseEnd.replace(':',"")):
            nowCourse = i
            break

    return nowCourse

def getNextLesson(termStartDate_str, courseJson_name, sectionJson_name):
    now = datetime.datetime.now()
    while True:
        tmp = getNowLesson(now.strftime("%Y-%m-%d %H:%M"), termStartDate_str, courseJson_name, sectionJson_name)
        if tmp:
            return tmp
        now += datetime.timedelta(minutes=5)

def getRecentLesson(termStartDate_str, courseJson_name, sectionJson_name):
    lessonList = []

    now = datetime.datetime.now()
    now -= datetime.timedelta(minutes=60)

    for i in range(int(120/5)+1):
        tmp = getNowLesson(now.strftime("%Y-%m-%d %H:%M"), termStartDate_str, courseJson_name, sectionJson_name)
        if tmp and tmp['name'] not in lessonList:
            lessonList.append(tmp['name'])
        now += datetime.timedelta(minutes=5)

    return lessonList

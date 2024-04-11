import requests

def pushNotice(text):
    return # 此处需要自定义
    return requests.get("https://push", params={
        "token": "xxx",
        "send": "1",
        "title": "学习通签到",
        "text": text
    }).text

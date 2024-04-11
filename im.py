import string
import secrets
import time
import json

def get_wsurl():
    s = ''.join(secrets.choice(string.ascii_lowercase + '012345') for _ in range(8))
    n = secrets.randbelow(1000)

    return f"wss://im-api-vip6-v2.easemob.com/ws/{n:03d}/{s}/websocket"

def build_login_msg(uid, token):
    b_time = str(int(time.time() * 1000)).encode()
    b_token = token.encode()
    size = len(uid)
    d = bytearray()
    d.extend(bytes([0x08, 0x00, 0x12, 0x34 + size, 0x0a, 0x0e]))
    d.extend(b'cx-dev#cxstudy')
    d.extend(bytes([0x12, size]))
    d.extend(uid.encode())
    d.extend(bytes([0x1a, 0x0b]))
    d.extend(b'easemob.com')
    d.extend(bytes([0x22, 0x13]))
    d.extend(b'webim_')
    d.extend(b_time)
    d.extend(bytes([0x1a, 0x85, 0x01, 0x24, 0x74, 0x24]))
    d.extend(b_token)
    d.extend(bytes([0x40, 0x03, 0x4a, 0xc0, 0x01, 0x08, 0x10, 0x12, 0x05, 0x33, 0x2e, 0x30, 0x2e, 0x30, 0x28, 0x00, 0x30, 0x00, 0x4a, 0x0d]))
    d.extend(b_time)
    d.extend(bytes([0x62, 0x05, 0x77, 0x65, 0x62, 0x69, 0x6d, 0x6a, 0x13, 0x77, 0x65, 0x62, 0x69, 0x6d, 0x5f]))
    d.extend(b_time)
    d.extend(bytes([0x72, 0x85, 0x01, 0x24, 0x74, 0x24]))
    d.extend(b_token)
    d.extend(bytes([0x50, 0x00, 0x58, 0x00]))
    return d



def get_chat_id(bytes_array):
    bytes_end = bytearray([0x1A, 0x16, 0x63, 0x6F, 0x6E, 0x66, 0x65, 0x72, 0x65, 0x6E, 0x63, 0x65, 0x2E, 0x65, 0x61, 0x73, 0x65, 0x6D, 0x6F, 0x62, 0x2E, 0x63, 0x6F, 0x6D])

    end = bytes_array.rfind(bytes_end)
    if end == -1:
        return None

    start = bytes_array[:end].rfind(0x12)
    if start == -1:
        return None

    length = bytes_array[start+1]
    return bytes_array[start+2: start+2+length].decode('utf-8')

def build_release_session_msg(chatID, session):
    size = len(chatID)
    d = bytearray()
    d.extend(bytes([0x08, 0x00, 0x40, 0x00, 0x4a]))
    d.extend(bytes([0x26 + size, 0x10]))
    d.extend(session)
    d.extend(bytes([0x1a, 0x29, 0x12, size]))
    d.extend(chatID.encode())
    d.extend(bytes([0x1a, 0x16]))
    d.extend(b'conference.easemob.com')
    d.extend(bytes([0x58, 0x00]))
    return d

def get_attachment(bytes_array, start, end):
    bytes_attachment = bytearray([0x0a, 0x61, 0x74, 0x74, 0x61, 0x63, 0x68, 0x6D, 0x65, 0x6E, 0x74, 0x10, 0x08, 0x32])

    start = bytes_array.find(bytes_attachment, start, end)
    if start == -1:
        return None
    start += len(bytes_attachment)

    length = bytes_array[start] + (bytes_array[start+1]-1)*0x80
    start += 2

    json_str = bytes_array[start:start+length].decode()

    return json.loads(json_str)

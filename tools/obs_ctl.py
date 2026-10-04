"""obs_ctl.py <RequestType> [json data]: one obs-websocket v5 request over a raw socket."""
import base64
import hashlib
import json
import os
import socket
import struct
import sys

# OBS_CONFIG overrides the config directory; the default is a scoop install's persisted one.
CONF = os.path.join(os.environ.get('OBS_CONFIG', os.path.expanduser(r'~\scoop\persist\obs-studio\config\obs-studio')),
                    'plugin_config', 'obs-websocket', 'config.json')
cfg = json.load(open(CONF, encoding='utf-8'))

sock = socket.create_connection(('127.0.0.1', cfg['server_port']), timeout=10)
key = base64.b64encode(os.urandom(16)).decode()
sock.sendall((f'GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
              f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n'
              f'Sec-WebSocket-Protocol: obswebsocket.json\r\n\r\n').encode())
head = b''
while b'\r\n\r\n' not in head:
    head += sock.recv(1)
if b' 101 ' not in head.split(b'\r\n')[0]:
    raise SystemExit(head.decode(errors='replace'))


def recv_exact(n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise SystemExit('connection closed')
        buf += chunk
    return buf


def send(obj):
    data = json.dumps(obj).encode()
    mask = os.urandom(4)
    n = len(data)
    header = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack('>H', n))
    sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def recv():
    b1, b2 = recv_exact(2)
    n = b2 & 0x7F
    if n == 126:
        n = struct.unpack('>H', recv_exact(2))[0]
    elif n == 127:
        n = struct.unpack('>Q', recv_exact(8))[0]
    return json.loads(recv_exact(n))


hello = recv()['d']
identify = {'rpcVersion': 1}
if 'authentication' in hello:
    a = hello['authentication']
    secret = base64.b64encode(hashlib.sha256((cfg['server_password'] + a['salt']).encode()).digest())
    identify['authentication'] = base64.b64encode(hashlib.sha256(secret + a['challenge'].encode()).digest()).decode()
send({'op': 1, 'd': identify})
while recv()['op'] != 2:
    pass

request = {'requestType': sys.argv[1], 'requestId': '1'}
if len(sys.argv) > 2:
    request['requestData'] = json.loads(sys.argv[2])
send({'op': 6, 'd': request})
while True:
    msg = recv()
    if msg['op'] == 7:
        print(json.dumps({'status': msg['d']['requestStatus'], 'data': msg['d'].get('responseData')}))
        break

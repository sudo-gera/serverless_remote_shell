from aiohttp import web
import aiohttp
import aiohttp.web
import asyncio
import base64
import sys
import termios
import copy
import time
from dataqueue import DataQueue

if len(sys.argv) < 2:
    print('run one of these:')
    print(f'''python {sys.argv[0]} [port] (host will be 0.0.0.0)''')
    print(f'''python {sys.argv[0]} [host] [port]''')
    exit()
if len(sys.argv) == 2:
    port=sys.argv[1]
    host='0.0.0.0'
else:
    host=sys.argv[1]
    port=sys.argv[2]

d={}

async def get(req):
    data=b''
    try:
        name=req.match_info['name']
        if name not in d:
            d[name]=DataQueue()
        data=await d[name].get_wait()
    finally:
        return aiohttp.web.Response(body=data)

async def post(req):
    name=req.match_info['name']
    if name not in d:
        d[name]=DataQueue()
    d[name].put(await req.read())
    return aiohttp.web.Response()

def start(req):
    name=base64.b64encode((round(time.time()*1000)&0xff_ff_ff_ff_ff_ff).to_bytes(6,'little')).decode().replace('/','_')
    print()
    print(f'host found! you can connect to it via')
    print(f'python remote.py http://[this server]:{port}/{name}')
    return aiohttp.web.Response(text=
        f'''export REMOTE_URL='http://{req.host}/{name}'\n'''+
        open('remote.sh').read()
    )


app = web.Application()
app.add_routes([
    web.get('/', start),
    web.get('/{name}', get),
    web.post('/{name}', post)
])

if __name__ == '__main__':
    print()
    print('Now run on host:')
    print()
    print(f'curl -s http://[this server]:{port} | bash')
    print()
    web.run_app(app,host=host, port=port)

import aiohttp
import asyncio
import base64
import sys
import termios
import copy
from dataqueue import DataQueue

class term_controller:
    def __init__(self) -> None:
        self.entered=0
    def __enter__(self):
        self.entered=1
        self.fd=sys.stdin.fileno()
        self.mode=termios.tcgetattr(self.fd)
        self.save=copy.copy(self.mode)
        self.mode[0] &= ~(termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON)
        self.mode[1] &= ~(termios.OPOST)
        self.mode[2] &= ~(termios.CSIZE | termios.PARENB)
        self.mode[2] |= termios.CS8
        self.mode[3] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        self.mode[6][termios.VMIN] = 1
        self.mode[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.mode)
        return self
    def __exit__(self,*a,**s):
        if self.entered:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.save)
            self.entered=0
            return True

term=term_controller()

running=1

url = sys.argv[1]

async def connect_stdin():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)
    return reader

async def read():
    e=await connect_stdin()
    async with aiohttp.ClientSession() as session:
        with term:
            while running:
                f=await e.read(1)
                async with session.post(url+'_server',data=f) as resp:
                    pass

async def write():
    async with aiohttp.ClientSession() as session:
        global running
        while running:
            try:
                async with session.get(url+'_client') as resp:
                    f=await resp.read()
                    t=[]
                    for w in f.split():
                        if w==b'^^^^':
                            running=0
                        else:
                            w=base64.b64decode(w)
                            if len(w)==2:
                                w=w[:-1]
                            t.append(w)
                    t=b''.join(t)
                    run=term.__exit__()
                    sys.stdout.buffer.write(t)
                    sys.stdout.buffer.flush()
                    if not running:
                        print('hit enter to close the connection...')
                    if run:
                        term.__enter__()
            except asyncio.TimeoutError:
                pass


async def main():
    asyncio.create_task(read())
    asyncio.create_task(write())
    await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})
    print('connection closed')

asyncio.run(main())

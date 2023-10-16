import aiohttp
import asyncio
import base64
import sys
import termios
import copy
import traceback
from dataqueue import DataQueue


class term_controller:
    def __init__(self) -> None:
        self.entered = 0

    def __enter__(self):
        self.entered = 1
        self.fd = sys.stdin.fileno()
        self.mode = termios.tcgetattr(self.fd)
        self.save = copy.copy(self.mode)
        self.mode[0] &= ~(termios.BRKINT | termios.ICRNL |
                          termios.INPCK | termios.ISTRIP | termios.IXON)
        self.mode[1] &= ~(termios.OPOST)
        self.mode[2] &= ~(termios.CSIZE | termios.PARENB)
        self.mode[2] |= termios.CS8
        self.mode[3] &= ~(termios.ECHO | termios.ICANON |
                          termios.IEXTEN | termios.ISIG)
        self.mode[6][termios.VMIN] = 1
        self.mode[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.mode)
        return self

    def __exit__(self, *a, **s):
        if self.entered:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.save)
            self.entered = 0
            return True


term = term_controller()

running = 1

url = sys.argv[1]

async def connect_stdin_stdout():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer



escape = b'~__.'

async def read(reader):
    async with aiohttp.ClientSession() as session:
        with term:
            try:
                esc_prefix = b''
                global running
                while running:
                    f = await reader.read(1)
                    esc_prefix += f
                    f = b''
                    if not escape.startswith(esc_prefix):
                        f = esc_prefix
                        esc_prefix = b''
                    if escape == esc_prefix:
                        running = 0
                    if f:
                        async with session.post(url + '_server', data=f) as resp:
                            pass
            except asyncio.CancelledError:
                async with session.post(url + '_server', data=b'\n') as resp:
                    pass
            except:
                print(traceback.format_exc())
                raise


async def write(writer, reader_task):
    async with aiohttp.ClientSession() as session:
        global running
        while running:
            try:
                async with session.get(url + '_client') as resp:
                    f = await resp.read()
                    t = []
                    for w in f.split():
                        if w == b'^^^^':
                            running = 0
                        else:
                            w = base64.b64decode(w)
                            t.append(w)
                    t = b''.join(t)
                    writer.write(t)
                    await writer.drain()
                    if not running:
                        reader_task.cancel()
                        # print('hit enter to close the connection...', end='\r\n')
            except asyncio.TimeoutError:
                pass

async def main():
    reader, writer = await connect_stdin_stdout()
    rt = asyncio.create_task(read(reader))
    asyncio.create_task(write(writer, rt))
    await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})
    print('connection closed')

asyncio.run(main())

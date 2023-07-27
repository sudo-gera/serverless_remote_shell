import asyncio
class DataQueue:
    def __init__(self):
        self.queue=asyncio.Queue()
        self.len=0
        self.lock=asyncio.Lock()
    def put(self,val:bytes):
        assert type(val) in [bytes, bytearray]
        self.queue.put_nowait(val)
        self.len+=len(val)
    def get(self):
        data=[]
        try:
            while 1:
                chunk=self.queue.get_nowait()
                self.len-=len(chunk)
                data.append(chunk)
        except asyncio.QueueEmpty:
            pass
        data=b''.join(data)
        return data
    def __len__(self):
        return self.len
    async def get_wait(self):
        async with self.lock:
            data=await self.queue.get()
            self.len-=len(data)
            g=self.get()
            data+=g
            return data

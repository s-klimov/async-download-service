import asyncio
from urllib.parse import urljoin

import aiohttp

SAVE_FILE_HOST = 'http://0.0.0.0:8080'
SAVE_FILE_URL = '/archive/save/'
CHUNK_SIZE = 2 ** 16
FILE_NAME = 'test_photos/7kna/2.jpg'


@aiohttp.streamer
def file_sender(writer, file_name = None):
    with open(file_name, 'rb') as f:
        chunk = f.read(CHUNK_SIZE)

        while chunk:
            yield from writer.write(chunk)
            chunk = f.read(CHUNK_SIZE)


async def main():
    url = urljoin(SAVE_FILE_HOST, SAVE_FILE_URL)
    async with aiohttp.ClientSession() as client:
        async with client.post(url, data=file_sender(file_name=FILE_NAME)) as resp:
            print(await resp.text())


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

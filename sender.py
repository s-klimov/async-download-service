import asyncio
import logging
import sys
from urllib.parse import urljoin

import aiohttp

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

SAVE_FILE_HOST = 'http://localhost:8080'
SAVE_FILE_URL = '/archive/save/'
CHUNK_SIZE = 2 ** 16
FILE_NAME = 'test_photos/7kna/2.jpg'


@aiohttp.streamer
def file_sender(writer, file_name):
    logger.debug(f'{CHUNK_SIZE=}')

    with open(file_name, 'rb') as f:
        chunk = f.read(CHUNK_SIZE)

        while chunk:
            logger.debug(f'send a chunk of the file {file_name}')
            yield from writer.write(chunk)
            chunk = f.read(CHUNK_SIZE)


async def main():
    url = urljoin(SAVE_FILE_HOST, SAVE_FILE_URL)
    async with aiohttp.ClientSession() as client:
        async with client.post(url, data=file_sender(file_name=FILE_NAME)) as resp:
            logger.info(await resp.text())


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

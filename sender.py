import asyncio
import logging
import sys
from urllib.parse import urljoin

import aiofiles
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


async def file_sender(file_name):
    logger.debug(f'{CHUNK_SIZE=}')

    async with aiofiles.open(file_name, 'rb') as f:
        chunk = await f.read(CHUNK_SIZE)

        while chunk:
            yield chunk
            chunk = await f.read(CHUNK_SIZE)


async def main():
    url = urljoin(SAVE_FILE_HOST, SAVE_FILE_URL)
    headers = {
        'CONTENT-DISPOSITION': f'attachment;filename={FILE_NAME}',
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=file_sender(file_name=FILE_NAME)) as resp:
            logger.info(await resp.text())


if __name__ == '__main__':

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

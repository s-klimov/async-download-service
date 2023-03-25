import logging
import os
import os.path
import signal
import sys

import aiofiles
import argparse
from aiohttp import web
import asyncio

from aiohttp.web_request import Request

APP_NAME = "Файловый сервис"
ARCHIVE_URL = "/archive/"
PHOTOS_PATH = os.getenv("PHOTOS_DIR", "test_photos/")
BATCH_SIZE = 512_000  # размер порции для отдачи файла в байтах
ARCHIVE_FILE_NAME = "archive.zip"
INTERVAL_SEC = 1  # временной интервал в секундах для искусственной задержки скачивания файла

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger(APP_NAME)


def handler(signum, frame):
    """Хендлер прерывания процесса архивации"""
    print('Signal handler called with signal', signum)
    pressed_key = input("Ctrl-c нажат. Внимание, текущие процессы архивации остановятся. "
                        "Действительно остановить сервис? y/n ").strip()
    if pressed_key == 'y':
        logger.info('Процесс архивации прекращен пользователем')
        raise KeyboardInterrupt


async def archive(request: Request) -> web.StreamResponse:
    """Хендлер формирования архива и скачивания его в файл"""

    archive_hash = request.match_info['archive_hash']
    folder_path = os.path.join(os.getcwd(), PHOTOS_PATH, archive_hash)

    if not (os.path.exists(folder_path) and os.path.isdir(folder_path)):
        logger.warning(f'Запрошена несуществующая папка {archive_hash}')
        raise web.HTTPNotFound(text='Архив не существует или был удален')

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'multipart/x-mixed-replace',
            'CONTENT-DISPOSITION': f'attachment;filename={ARCHIVE_FILE_NAME}'
        }
    )

    process = await asyncio.create_subprocess_exec(
        'zip',
        '-r', '-', '.',  # забираем в архив все файлы и папки из директории, указанной в cwd
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=os.path.join(PHOTOS_PATH, archive_hash),
    )

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)

    try:
        while not process.stdout.at_eof():
            logger.debug("Sending archive chunk ...")
            archive_data = await process.stdout.read(BATCH_SIZE)

            await response.write(archive_data)
            if request.app.debug:
                await asyncio.sleep(INTERVAL_SEC)
            signal.signal(signal.SIGINT, handler)

    except asyncio.CancelledError:
        logger.error("Download was interrupted ")

        # отпускаем перехваченный CancelledError
        raise
    finally:
        # если процесс не завершился, то принудительно его "убиваем"
        # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.returncode
        logger.info("Terminate zip process")
        if process.returncode is None:
            process.kill()
            await process.communicate()

    return response


async def handle_index_page(request):
    """Главная страница проекта"""

    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def get_args() -> [str, bool]:
    """Достает для проекта значения параметров командной строки"""
    parser = argparse.ArgumentParser(description='Сервер архивирования медиа-файлов')
    parser.add_argument('-l', '--level', nargs='?', choices=['debug', 'info', 'warning', 'error'], default='info',
                        help='уровень логирования в консоль (default: %(default)s)')
    parser.add_argument('-d', '--delay', action='store_true',
                        help='включить задержку ответа')
    args = parser.parse_args()
    return args.level, args.delay


if __name__ == '__main__':

    logger_level, delay = get_args()

    logger.setLevel(getattr(logging, logger_level.upper()))
    app = web.Application(debug=delay)
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)

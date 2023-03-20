import asyncio
import logging

import subprocess

import argparse


BATCH_SIZE = 512_000  # размер порции для отдачи файла в байтах

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)


async def main(paths: list[str], save: str | None) -> None:
    """Создаёт архив и помещает его содержимое в переменную archive

    Ключевые аргументы:
    paths -- список файлов и папок для архивации
    save -- имя файла архива, необязательный параметр
    """

    process = subprocess.check_output("pwd")
    logging.info("текущая папка %s", (process, ))

    cmd = " ".join(["zip", "-r", "-", *paths])

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if save is None:
        return

    counter = 1
    archive_size = 0

    while True:
        logging.info("проход № %s" % (counter, ))
        mode = "wb" if counter == 1 else "ab"
        archive = await proc.stdout.read(BATCH_SIZE)
        archive_size += len(archive)
        with open(save, mode) as fh:
            fh.write(archive)

        counter += 1

        if proc.stdout.at_eof():
            break

    logging.info("размер архива %.f байт" % (archive_size, ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Получение списка файлов/папок для архивации.')
    parser.add_argument('paths', metavar='N', type=str, nargs='+',
                        help='список файлов/папок')
    parser.add_argument('--save', type=str,
                        help='имя файла архива')

    args = parser.parse_args()

    asyncio.run(main(args.paths, args.save))

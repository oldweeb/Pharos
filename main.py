import asyncio
import urllib3
import sys
from loguru import logger

from bootstrap.container import container
import runner
from features import swaps, checkin
import services

log_format = (
    "<light-blue>[</light-blue><yellow>{time:HH:mm:ss}</yellow><light-blue>]</light-blue> | "
    "<level>{level: <8}</level> | "
    "<cyan>{file}:{line}</cyan> | "
    "<level>{message}</level>"
)

def configure():
    container.init_resources()
    container.wire(modules=[runner, swaps, checkin, services, __name__])

async def start():
    runner = container.runner()
    await runner.run()

async def cleanup():
    web3 = container.web3()
    if web3 and web3.provider:
        await web3.provider._session.close()

async def main():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format=log_format
    )
    logger.add(
        'logs/app.log',
        rotation='10 MB',
        retention='1 month',
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}",
        level="INFO",
    )

    configure()
    try:
        await start()
    finally:
        await cleanup()


if __name__ == '__main__':
    asyncio.run(main())
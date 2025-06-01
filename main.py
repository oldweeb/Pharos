import asyncio
import urllib3
import sys
from loguru import logger
import platform

from bootstrap.container import container
import runner
from features import faucet, swaps, checkin, liquidity
import services

log_format = (
    "<light-blue>[</light-blue><yellow>{time:HH:mm:ss}</yellow><light-blue>]</light-blue> | "
    "<level>{level: <8}</level> | "
    "<cyan>{file}:{line}</cyan> | "
    "<level>{message}</level>"
)

def configure():
    container.init_resources()
    container.wire(modules=[runner, swaps, checkin, faucet, services, liquidity, __name__])

async def start():
    runner = container.runner()
    await runner.run()

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
    await start()


if __name__ == '__main__':
    if platform.system() == 'Windows':
        # Use SelectorEventLoop instead of ProactorEventLoop on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
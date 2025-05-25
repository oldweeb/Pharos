import asyncio
import random
from eth_account import Account
import httpx
from constants.api import CHECKIN_API_URL
from features.base import BaseFeature
from models.configuration import AccountConfig, CheckinSettings
from loguru._logger import Logger
from bootstrap.container import ApplicationContainer
from dependency_injector.wiring import inject, Provide


class CheckIn(BaseFeature):
    @inject
    def __init__(
        self, 
        settings: CheckinSettings = Provide[ApplicationContainer.checkin_settings],
        logger: Logger = Provide[ApplicationContainer.logger]
    ):
        self._settings = settings
        self._logger = logger
    
    @property
    def name(self) -> str:
        return 'checkin'

    async def execute(self, account_config: AccountConfig):
        if not self._settings.enabled:
            self._logger.info(f'Checkin feature is disabled, skipping...')
            return
        
        account = Account.from_key(account_config.private_key)
        endpoint = CHECKIN_API_URL.format(address=account.address)
        self._logger.info(f'[{account.address}] Sending request to {endpoint}')

        for i in range(self._settings.retry_count):
            self._logger.info(f'[{account.address}] Checkin Attempt {i + 1}/{self._settings.retry_count}')
            async with httpx.AsyncClient() as client:
                headers = {
                    "accept": "application/json, text/plain, */*",
                    "authorization": f"Bearer {account_config.auth_key}",
                    "priority": "u=1, i",
                    "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "\"Windows\"",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-site",
                    "Origin": "https://testnet.pharosnetwork.xyz",
                    "Referer": "https://testnet.pharosnetwork.xyz/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                }

                try:
                    response = await client.post(endpoint, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    self._logger.success(f'[{account.address}] ✅ Checkin successful: {data["msg"]}')
                    break
                except httpx.HTTPStatusError as e:
                    self._logger.error(f'[{account.address}] ❌ Checkin request error: {e}')
                except httpx.RequestError as e:
                    self._logger.error(f'[{account.address}] ❌ Checkin request error: {e}')
                finally:
                    sleep_time = random.randint(self._settings.pause_between_attemps[0], self._settings.pause_between_attemps[1])
                    self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before next checkin attempt')
                    await asyncio.sleep(sleep_time)
        

from eth_account import Account
import httpx
from loguru._logger import Logger
from dependency_injector.wiring import inject, Provide
from twocaptcha import TwoCaptcha
from datetime import datetime
from eth_account.signers.local import LocalAccount

from bootstrap.container import ApplicationContainer
from constants.api import FAUCET_API_URL, FAUCET_CHECK_API_URL
from constants.captcha import CAPTCHA_KEY, CAPTCHA_SITEURL
from features.base import BaseFeature
from models.configuration import AccountConfig, FaucetSettings


class Faucet(BaseFeature):
    @inject
    def __init__(
        self,
        settings: FaucetSettings = Provide[ApplicationContainer.faucet_settings],
        logger: Logger = Provide[ApplicationContainer.logger],
    ):
        self._settings = settings
        self._logger = logger
        

    @property
    def name(self) -> str:
        return 'faucet'

    async def execute(self, account_config: AccountConfig) -> None:
        if not self._settings.enabled:
            self._logger.info(f'Faucet feature is disabled, skipping...')
            return

        account = Account.from_key(account_config.private_key)
        if await self._check_is_claimed(account, account_config):
            return

        solver = TwoCaptcha(self._settings.twocaptcha_key)
        for i in range(self._settings.retry_captcha):
            try:
                self._logger.info(f'[{account.address}] Solving captcha for account. Attempt {i + 1}/{self._settings.retry_captcha}')
                captcha_result = solver.recaptcha(
                    sitekey=CAPTCHA_KEY,
                    url=CAPTCHA_SITEURL,
                    proxy={
                        "type": "HTTP",
                        "uri": account_config.proxy.replace('http://', '')
                    } if account_config.proxy else None
                )

                self._logger.success(f'[{account.address}] ✅ Captcha solved')
                break
            except Exception as e:
                self._logger.error(f'[{account.address}] Error solving captcha: {e}')
                if i == self._settings.retry_captcha - 1:
                    self._logger.error(f'[{account.address}] ❌ Failed to solve captcha after {self._settings.retry_captcha} attempts')
                    return
        
        for i in range(self._settings.retry_count):
            try:
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
                self._logger.info(f'[{account.address}] Claiming faucet for account. Attempt {i + 1}/{self._settings.retry_count}')
                async with httpx.AsyncClient() as client:
                    response = await client.post(FAUCET_API_URL.format(address=account.address), headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    self._logger.success(f'[{account.address}] ✅ Faucet claimed: {data["msg"]}')
                    break
            except httpx.HTTPStatusError as e:
                self._logger.error(f'[{account.address}] ❌ Faucet claim request error: {e}')
        
    async def _check_is_claimed(self, account: LocalAccount, account_config: AccountConfig) -> bool:
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
            endpoint = FAUCET_CHECK_API_URL.format(address=account.address)
            self._logger.info(f'[{account.address}] Checking if faucet is claimed.')
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=headers)
                response.raise_for_status()
                data = response.json()
                claimed = data['data']['is_able_to_faucet'] == False
                if claimed:
                    next_claim_time = datetime.fromtimestamp(data['data']['avaliable_timestamp'])
                    self._logger.info(f'[{account.address}] Faucet is already claimed. Next claim will be available at {next_claim_time}')
                    return True
                else:
                    self._logger.info(f'[{account.address}] Faucet is not claimed.')
                    return False
        except httpx.HTTPStatusError as e:
            self._logger.error(f'[{account.address}] ❌ Failed to check faucet status: {e}')
            return False

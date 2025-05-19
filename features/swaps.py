import web3
from dependency_injector.wiring import inject, Provide
from loguru._logger import Logger
from web3 import AsyncWeb3

from bootstrap.container import ApplicationContainer
from features.base import BaseFeature
from models.configuration import SwapsSettings, Account


class Swaps(BaseFeature):
    @inject
    def __init__(
        self,
        settings: SwapsSettings = Provide[ApplicationContainer.swaps_settings],
        logger: Logger = Provide[ApplicationContainer.logger]
    ):
        self._settings = settings
        self._logger = logger

    async def execute(self, account: Account):
        web3_account = web3.Account.from_key(account.private_key)
        web3 = AsyncWeb3
        pass
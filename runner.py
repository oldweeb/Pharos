from abc import ABC, abstractmethod
import random

import inject
from features.base import BaseFeature
from models.configuration import Configuration, AccountsMode, AccountConfig, Settings
from loguru._logger import Logger

class BaseRunner(ABC):
    def __init__(self, features: list[BaseFeature]):
        self._features = features

    @abstractmethod
    async def run(self):
        pass

    async def _run_account(self, account: AccountConfig, settings: Settings):
        features: list[BaseFeature] = self._features
        if settings.randomize_feature_order:
            features = random.shuffle(self._features)
        
        for feature in features:
            self._logger.info(f'Running feature: {feature.name}')
            await feature.execute(account)
            

class ParallelRunner(BaseRunner):
    def __init__(self, features: list[BaseFeature], configuration: Configuration, logger: Logger):
        super().__init__(features)
        self._configuration = configuration
        self._logger = logger

    async def run(self):
        self._logger.info(f"Running in parallel, number of accounts: {len(self._configuration.accounts)}")
        pass

class SequentialRunner(BaseRunner):
    def __init__(self, features: list[BaseFeature], configuration: Configuration, logger: Logger):
        super().__init__(features)
        self._configuration = configuration
        self._logger = logger

    async def run(self):
        self._logger.info(f"Running sequentially, number of accounts: {len(self._configuration.accounts)}")
        for account in self._configuration.accounts:
            await self._run_account(account, self._configuration.settings)
        pass

class RunnerFactory:
    def __init__(self, features: list[BaseFeature], configuration: Configuration, logger: Logger):
        self._configuration = configuration
        self._logger = logger
        self._features = features

    def create(self) -> BaseRunner:
        if self._configuration.settings.accounts_mode == AccountsMode.PARALLEL:
            return ParallelRunner(self._features, self._configuration, self._logger)

        return SequentialRunner(self._features, self._configuration, self._logger)

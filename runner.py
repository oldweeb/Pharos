from abc import ABC, abstractmethod
from models.configuration import Configuration, AccountsMode, Account, Settings
from loguru._logger import Logger

class BaseRunner(ABC):
    @abstractmethod
    async def run(self):
        pass

    async def __run_account__(self, account: Account, settings: Settings):
        pass

class ParallelRunner(BaseRunner):
    def __init__(self, configuration: Configuration, logger: Logger):
        self._configuration = configuration
        self._logger = logger

    async def run(self):
        self._logger.info(f"Running in parallel, number of accounts: {len(self._configuration.accounts)}")
        pass

class SequentialRunner(BaseRunner):
    def __init__(self, configuration: Configuration, logger: Logger):
        self._configuration = configuration
        self._logger = logger

    async def run(self):
        self._logger.info(f"Running sequentially, number of accounts: {len(self._configuration.accounts)}")
        for account in self._configuration.accounts:
            await self.__run_account__(account, self._configuration.settings)
        pass

class RunnerFactory:
    def __init__(self,configuration: Configuration, logger: Logger):
        self._configuration = configuration
        self._logger = logger

    def create(self) -> BaseRunner:
        if self._configuration.settings.accounts_mode == AccountsMode.PARALLEL:
            return ParallelRunner(self._configuration, self._logger)

        return SequentialRunner(self._configuration, self._logger)

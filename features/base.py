from abc import ABC, abstractmethod

from models.configuration import AccountConfig


class BaseFeature(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def execute(self, account: AccountConfig):
        pass
from abc import ABC, abstractmethod

from models.configuration import Account


class BaseFeature(ABC):
    @abstractmethod
    async def execute(self, account: Account):
        pass
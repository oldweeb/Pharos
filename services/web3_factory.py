from web3 import AsyncHTTPProvider, AsyncWeb3
from constants.chain import RPC_URL
from models.configuration import AccountConfig
import platform
import aiohttp


class Web3Factory:
    def __init__(self, account_config: AccountConfig):
        self.rpc_url = RPC_URL
        self.web3 = None
        self.account = account_config
    
    async def __aenter__(self):
        request_kwargs = {
            "proxy": self.account.proxy if self.account.proxy else None,
            "ssl": False
        }

        self.provider = AsyncHTTPProvider(
            self.rpc_url,
            request_kwargs=request_kwargs
        )
        self.web3 = AsyncWeb3(self.provider)
        return self.web3
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.provider.disconnect()

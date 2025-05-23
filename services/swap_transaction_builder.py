from typing import Self

from web3 import AsyncHTTPProvider, AsyncWeb3
from eth_account.signers.local import LocalAccount

from constants.abi import ABI
from constants.chain import CHAIN_ID, RPC_URL
from constants.contracts import TOKENS
from services.gas_helper import GasHelper


class SwapTransactionBuilder:
    def __init__(self):
        self._in = ''
        self._out = ''
        self._amount = 0
        self._account = None

    def with_in(self, token_in: str) -> Self:
        self._in = token_in
        return self
    
    def with_out(self, token_out: str) -> Self:
        self._out = token_out
        return self

    def with_amount(self, amount: int) -> Self:
        self._amount = amount
        return self
    
    def with_account(self, account: LocalAccount) -> Self:
        self._account = account
        return self

    async def build(self) -> dict:
        if self._account is None:
            raise ValueError('Account is not set')
        
        web3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
        if self._in == 'PHRS' and self._out == 'WPHRS':
            return await self._build_wrap_transaction(web3)
        if self._in == 'WPHRS' and self._out == 'PHRS':
            return await self._build_unwrap_transaction(web3)
        return await self._build_swap_transaction(web3)

    async def _build_wrap_transaction(self, web3: AsyncWeb3) -> dict:
        wphrs_contract = web3.eth.contract(address=TOKENS['WPHRS'], abi=ABI['weth'])
        deposit_func = wphrs_contract.functions.deposit()

        nonce = await web3.eth.get_transaction_count(self._account.address, 'latest')

        transaction = {
            "from": self.account.address,
            "to": TOKENS['WPHRS'],
            "value": self._amount,
            "data": deposit_func._encode_transaction_data(),
            "chainId": CHAIN_ID,
            "type": 2,
            "nonce": nonce,
        }

        gas = await GasHelper.estimate_gas(web3, transaction)
        gas_price = await GasHelper.get_gas_price(web3)
        gas_params = await GasHelper.get_gas_params(web3)

        transaction.update({
            'gas': gas,
            'gasPrice': gas_price,
            **gas_params,
        })
        return transaction

    async def _build_unwrap_transaction(self, web3: AsyncWeb3) -> dict:
        wphrs_contract = web3.eth.contract(address=TOKENS['WPHRS'], abi=ABI['weth'])
        withdraw_func = wphrs_contract.functions.withdraw(self._amount)

        nonce = await web3.eth.get_transaction_count(self._account.address, 'latest')

        transaction = {
            "from": self._account.address,
            "to": TOKENS['WPHRS'],
            "value": 0,
            "data": withdraw_func._encode_transaction_data(),
            "chainId": CHAIN_ID,
            "type": 2,
            "nonce": nonce,
        }

        gas = await GasHelper.estimate_gas(web3, transaction)
        gas_price = await GasHelper.get_gas_price(web3)
        gas_params = await GasHelper.get_gas_params(web3)

        transaction.update({
            'gas': gas,
            'gasPrice': gas_price,
            **gas_params,
        })
        return transaction

    async def _build_swap_transaction(self, web3: AsyncWeb3) -> dict:
        pass

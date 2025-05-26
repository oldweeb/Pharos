from typing import Self

from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount

from constants.abi import ABI
from constants.chain import CHAIN_ID
from constants.contracts import TOKENS
from services.gas_helper import GasHelper


class SwapTransactionBuilder:
    def __init__(self):
        self._in = ''
        self._out = ''
        self._amount = 0
        self._account = None
        self._router_contract = None
        self._router_abi = None
        self._web3 = None
        self._slippage = 0.99  # 1% slippage protection

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
    
    def with_router(self, router_contract: str, router_abi: dict | list) -> Self:
        self._router_contract = router_contract
        self._router_abi = router_abi
        return self

    def with_web3(self, web3: AsyncWeb3) -> Self:
        self._web3 = web3
        return self

    async def build(self) -> dict:
        if self._account is None:
            raise ValueError('Account is not set')
        if self._web3 is None:
            raise ValueError('Web3 instance is not set')
        
        if self._in == 'PHRS' and self._out == 'WPHRS':
            return await self._build_wrap_transaction()
        if self._in == 'WPHRS' and self._out == 'PHRS':
            return await self._build_unwrap_transaction()
        return await self._build_swap_transaction()

    async def _build_wrap_transaction(self) -> dict:
        wphrs_contract = self._web3.eth.contract(
            address=self._web3.to_checksum_address(TOKENS['WPHRS']), 
            abi=ABI['weth']
        )
        deposit_func = wphrs_contract.functions.deposit()

        nonce = await self._web3.eth.get_transaction_count(self._account.address, 'latest')

        transaction = {
            "from": self._account.address,
            "to": self._web3.to_checksum_address(TOKENS['WPHRS']),
            "value": self._amount,
            "data": deposit_func._encode_transaction_data(),
            "chainId": CHAIN_ID,
            "type": 2,
            "nonce": nonce,
        }

        await self._set_gas(transaction)
        return transaction

    async def _build_unwrap_transaction(self) -> dict:
        wphrs_contract = self._web3.eth.contract(
            address=self._web3.to_checksum_address(TOKENS['WPHRS']), 
            abi=ABI['weth']
        )
        withdraw_func = wphrs_contract.functions.withdraw(self._amount)

        nonce = await self._web3.eth.get_transaction_count(self._account.address, 'latest')

        transaction = {
            "from": self._account.address,
            "to": self._web3.to_checksum_address(TOKENS['WPHRS']),
            "value": 0,
            "data": withdraw_func._encode_transaction_data(),
            "chainId": CHAIN_ID,
            "type": 2,
            "nonce": nonce,
        }

        await self._set_gas(transaction)
        return transaction

    async def _build_swap_transaction(self) -> dict:
        router = self._web3.eth.contract(
            address=self._web3.to_checksum_address(self._router_contract), 
            abi=self._router_abi
        )

        swap_data = router.encode_abi('exactInputSingle', args=[{
            'tokenIn': self._web3.to_checksum_address(TOKENS[self._in]),
            'tokenOut': self._web3.to_checksum_address(TOKENS['WPHRS']) \
                        if self._out == 'PHRS' \
                        else self._web3.to_checksum_address(TOKENS[self._out]),
            'fee': 10000,
            'recipient': self._account.address,
            'amountIn': self._amount,
            'amountOutMinimum': 0,
            'sqrtPriceLimitX96': 0
        }]) \
        if self._in != 'PHRS' \
        else router.encode_abi('exactInput', args=[{
            'path': self._get_path(),
            'recipient': self._account.address,
            'amountIn': self._amount,
            'deadline': await self._get_deadline(),
        }])

        multicall_data = [swap_data]
        if self._out == 'PHRS':
            unwrap_data = router.encode_abi('unwrapWETH9', args=[0, self._account.address])
            multicall_data.append(unwrap_data)
        
        # Only include value if swapping from native token
        value = self._amount if self._in == 'PHRS' else 0

        # Final calldata for multicall(deadline, data[])
        deadline = await self._get_deadline()
        multicall_encoded = router.encode_abi('multicall', args=[deadline, multicall_data])

        base_tx = {
            'from': self._account.address,
            'to': router.address,
            'nonce': await self._web3.eth.get_transaction_count(self._account.address, 'latest'),
            'value': value,
            'chainId': CHAIN_ID,
            'data': multicall_encoded
        }

        await self._set_gas(base_tx)
        return base_tx
    
    def _get_path(self) -> bytes:
        path = [ 
            AsyncWeb3.to_bytes(hexstr=TOKENS['WPHRS']), 
            (500).to_bytes(3, 'big'),
            AsyncWeb3.to_bytes(hexstr=TOKENS[self._out]) 
        ]
    
        return b''.join(path)


    async def _get_deadline(self) -> int:
        return (await self._web3.eth.get_block('latest'))['timestamp'] + 1200

    async def _set_gas(self, tx: dict) -> None:
        gas = await GasHelper.estimate_gas(self._web3, tx)
        gas_params = await GasHelper.get_gas_params(self._web3)

        tx.update({
            'gas': gas,
            **gas_params,
        })

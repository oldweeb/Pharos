import asyncio
import random
from typing import Tuple
from dependency_injector.wiring import inject, Provide
from eth_account import Account
from loguru._logger import Logger
from web3 import AsyncHTTPProvider, AsyncWeb3
from eth_account.signers.local import LocalAccount

from bootstrap.container import ApplicationContainer
from constants.chain import RPC_URL
from constants.contracts import TOKENS
from constants.delay import MAX_SLEEP, MIN_SLEEP
from features.base import BaseFeature
from models.configuration import SwapsSettings, AccountConfig
from services.balance_checker import BalanceChecker


class Swaps(BaseFeature):
    @inject
    def __init__(
        self,
        balance_checker: BalanceChecker = Provide[ApplicationContainer.balance_checker],
        settings: SwapsSettings = Provide[ApplicationContainer.swaps_settings],
        logger: Logger = Provide[ApplicationContainer.logger]
    ):
        self._balance_checker = balance_checker
        self._settings = settings
        self._logger = logger
        self._web3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
        self._pairs = [
            { 'in': 'PHRS', 'out': 'USDT' },
            { 'in': 'PHRS', 'out': 'USDC' },
            { 'in': 'PHRS', 'out': 'WPHRS' },
            { 'in': 'USDT', 'out': 'PHRS' },
            { 'in': 'USDC', 'out': 'PHRS' },
            { 'in': 'WPHRS', 'out': 'PHRS' },
            { 'in': 'WPHRS', 'out': 'USDT' },
            { 'in': 'WPHRS', 'out': 'USDC' },
            { 'in': 'USDC', 'out': 'WPHRS' },
            { 'in': 'USDT', 'out': 'WPHRS' },
        ]
    
    @property
    def name(self) -> str:
        return 'swaps'

    async def execute(self, account_config: AccountConfig):
        account = Account.from_key(account_config.private_key)
        token_balances = await self._fetch_token_balances(account)
        self._logger.info(f'[{account.address}] Fetched tokens')
        self._display_token_balances(account, token_balances)

        count_of_swaps = random.randint(self._settings.count_of_swaps[0], self._settings.count_of_swaps[1])
        self._logger.info(f'[{account.address}] Will execute {count_of_swaps} swaps')
        sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)   
        self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before swapping')
        await asyncio.sleep(sleep_time)
        for i in range(count_of_swaps):
            self._logger.info(f'[{account.address}] Executing swap #{i + 1}')
            await self._execute_swap(account)

        
    async def _execute_swap(self, account: LocalAccount) -> None:
        valid_tokens = await self._filter_out_insufficient_balances(account)
            
        valid_pairs = [pair for pair in self._pairs if pair['in'] in valid_tokens]
        
        if not valid_pairs: 
            self._logger.warning(f'[{account.address}] No valid pairs found for swapping')
            return
            
        pair = random.choice(valid_pairs)
        balance, decimals = await self._balance_checker.get_balance(TOKENS[pair['in']]) \
                            if pair['in'] != 'PHRS' \
                            else await self._balance_checker.get_native_balance(account)
        
        swap_amount = balance * self._settings.percentage_of_balance / 100
        self._logger.info(f'[{account.address}] Swapping {(swap_amount / 10 ** decimals):.4f} {pair["in"]} to {pair["out"]}')
        
            

        pass    

    async def _fetch_token_balances(self, account: LocalAccount) -> list[Tuple[str, Tuple[int, int]]]:
        balances = []

        native_balance, native_decimals = await self._balance_checker.get_native_balance(account)
        balances.append(('PHRS', (native_balance, native_decimals)))
        for token in TOKENS:
            balance, decimals = await self._balance_checker.get_balance(TOKENS[token], account)
            balances.append((token, (balance, decimals)))
        
        return balances
    
    def _display_token_balances(self, account: LocalAccount, balances: list[Tuple[str, Tuple[int, int]]]) -> None:
        for token, (balance, decimals) in balances:
            formatted_balance = balance / 10 ** decimals
            self._logger.info(f'[{account.address}]: {formatted_balance:.4f} {token}')

    async def _filter_out_insufficient_balances(self, account: LocalAccount) -> list[str]:
        filtered_tokens = []
        for token in TOKENS:
            balance, decimals = await self._balance_checker.get_balance(TOKENS[token], account)
            if balance / 10 ** decimals > 0.001:
                filtered_tokens.append(token)
            else:
                self._logger.warning(f'[{account.address}] Insufficient balance for {token} to swap')
                
        return filtered_tokens
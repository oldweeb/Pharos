import asyncio
import random
from typing import Tuple
from dependency_injector.wiring import inject, Provide
from eth_account import Account
from loguru._logger import Logger
from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount

from bootstrap.container import ApplicationContainer
from constants.abi import ABI
from constants.contracts import SWAP_ROUTER_ADDRESS, TOKENS
from constants.delay import MAX_SLEEP, MIN_SLEEP
from features.base import BaseFeature
from models.configuration import SwapsSettings, AccountConfig
from services.approval_service import ApprovalService
from services.balance_checker import BalanceChecker
from services.swap_transaction_builder import SwapTransactionBuilder
from services.explorer_helper import ExplorerHelper
from services.web3_factory import Web3Factory

class Swaps(BaseFeature):
    @inject
    def __init__(
        self,
        balance_checker: BalanceChecker = Provide[ApplicationContainer.balance_checker],
        settings: SwapsSettings = Provide[ApplicationContainer.swaps_settings],
        approval_service: ApprovalService = Provide[ApplicationContainer.approval_service],
        logger: Logger = Provide[ApplicationContainer.logger]
    ):
        self._balance_checker = balance_checker
        self._settings = settings
        self._logger = logger
        self._approval_service = approval_service
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
        async with Web3Factory(account_config) as web3:
            account = Account.from_key(account_config.private_key)
            token_balances = await self._fetch_token_balances(account_config,account)
            self._logger.info(f'[{account.address}] Fetched tokens')
            self._display_token_balances(account, token_balances)

            count_of_swaps = random.randint(self._settings.count_of_swaps[0], self._settings.count_of_swaps[1])
            self._logger.info(f'[{account.address}] Will execute {count_of_swaps} swaps')
            sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)   
            self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before swapping')
            await asyncio.sleep(sleep_time)
            for i in range(count_of_swaps):
                self._logger.info(f'[{account.address}] Executing swap #{i + 1}')
                await self._execute_swap(account_config, account, web3)

        
    async def _execute_swap(self, account_config: AccountConfig, account: LocalAccount, web3: AsyncWeb3) -> None:
        valid_tokens = await self._filter_out_insufficient_balances(account_config, account)
            
        valid_pairs = [pair for pair in self._pairs if pair['in'] in valid_tokens]
        
        if not valid_pairs: 
            self._logger.warning(f'[{account.address}] No valid pairs found for swapping')
            return
            
        pair = random.choice(valid_pairs)
        balance, decimals = await self._balance_checker.get_balance(account_config, TOKENS[pair['in']], account) \
                            if pair['in'] != 'PHRS' \
                            else await self._balance_checker.get_native_balance(account, account_config)
        
        swap_percentage = random.randint(self._settings.percentage_of_balance[0], self._settings.percentage_of_balance[1])
        swap_amount = int(balance * swap_percentage / 100)
        
        for i in range(self._settings.retry_count):
            self._logger.info(f'[{account.address}] Attempt {i + 1}: Swapping {(swap_amount / 10 ** decimals):.4f} {pair["in"]} to {pair["out"]}')
            try:
                if pair['in'] != 'PHRS':
                    await self._approval_service.approve_token(account_config, account, TOKENS[pair['in']], SWAP_ROUTER_ADDRESS, swap_amount)
                
                transaction = await SwapTransactionBuilder() \
                    .with_in(pair['in']) \
                    .with_out(pair['out']) \
                    .with_amount(swap_amount) \
                    .with_account(account) \
                    .with_web3(web3) \
                    .with_router(SWAP_ROUTER_ADDRESS, ABI['swap_router']) \
                    .build()
                
                signed_tx = account.sign_transaction(transaction)
                
                tx_hash = await web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = await web3.eth.wait_for_transaction_receipt(tx_hash)
                
                tx_url = ExplorerHelper.get_tx_url(tx_hash)
                
                if receipt['status'] == 1:
                    self._logger.success(f'[{account.address}] ✅ Swap transaction was successful: {tx_url}')
                    break
                else:
                    self._logger.error(f'[{account.address}] ❌ Swap transaction failed: {tx_url}')
                
            except Exception as e:
                self._logger.error(f'[{account.address}] Error during a swap: {e}')
            finally:
                sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)   
                self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before next swap')
                await asyncio.sleep(sleep_time)

    async def _fetch_token_balances(self, account_config: AccountConfig, account: LocalAccount) -> list[Tuple[str, Tuple[int, int]]]:
        balances = []

        native_balance, native_decimals = await self._balance_checker.get_native_balance(account, account_config)
        balances.append(('PHRS', (native_balance, native_decimals)))
        for token in TOKENS:
            balance, decimals = await self._balance_checker.get_balance(account_config, TOKENS[token], account)
            balances.append((token, (balance, decimals)))
        
        return balances
    
    def _display_token_balances(self, account: LocalAccount, balances: list[Tuple[str, Tuple[int, int]]]) -> None:
        for token, (balance, decimals) in balances:
            formatted_balance = balance / 10 ** decimals
            self._logger.info(f'[{account.address}]: {formatted_balance:.4f} {token}')

    async def _filter_out_insufficient_balances(self, account_config: AccountConfig, account: LocalAccount) -> list[str]:
        filtered_tokens = []
        balance, decimals = await self._balance_checker.get_native_balance(account, account_config)
        if balance / 10 ** decimals > 0.001:
            filtered_tokens.append('PHRS')
        else:
            self._logger.warning(f'[{account.address}] Insufficient balance for PHRS to swap')

        for token in TOKENS:
            balance, decimals = await self._balance_checker.get_balance(account_config, TOKENS[token], account)
            if balance / 10 ** decimals > 0.001:
                filtered_tokens.append(token)
            else:
                self._logger.warning(f'[{account.address}] Insufficient balance for {token} to swap')
                
        return filtered_tokens
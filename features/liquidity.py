import asyncio
from datetime import datetime, timedelta
import random
from eth_account import Account
import httpx
from loguru._logger import Logger
from web3 import AsyncWeb3
from bootstrap.container import ApplicationContainer
from constants.abi import ABI
from constants.api import FETCH_POOLS_QUERY
from constants.chain import CHAIN_ID, MAX_TICK
from constants.contracts import LIQUIDITY_ROUTER_ADDRESS, TOKENS
from constants.delay import MAX_SLEEP, MIN_SLEEP
from features.base import BaseFeature
from models.configuration import AccountConfig, LiquiditySettings
from dependency_injector.wiring import inject, Provide
from eth_account.signers.local import LocalAccount
from eth_abi import decode

from models.liquidity import LiquidityPool, LiquidityPoolToken
from services.approval_service import ApprovalService
from services.balance_checker import BalanceChecker
from services.explorer_helper import ExplorerHelper
from services.gas_helper import GasHelper
from services.web3_factory import Web3Factory

class Liquidity(BaseFeature):
    @inject
    def __init__(
        self,
        balance_checker: BalanceChecker = Provide[ApplicationContainer.balance_checker],
        approval_service: ApprovalService = Provide[ApplicationContainer.approval_service],
        settings: LiquiditySettings = Provide[ApplicationContainer.liquidity_settings],
        logger: Logger = Provide[ApplicationContainer.logger],
    ):
        self._balance_checker = balance_checker
        self._approval_service = approval_service
        self._settings = settings
        self._logger = logger
    
    @property
    def name(self) -> str:
        return 'liquidity'
    
    async def execute(self, account_config: AccountConfig) -> None:
        if not self._settings.enabled:
            self._logger.info(f'Liquidity feature is disabled, skipping...')
            return
        
        account = Account.from_key(account_config.private_key)

        for i in range(self._settings.retry_count):
            self._logger.info(f'[{account.address}] Fetching pools, attempt {i + 1}/{self._settings.retry_count}')
            pools = await self._fetch_pools()
            if pools:
                break

            sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)   
            self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before next attempt')
            await asyncio.sleep(sleep_time)
            
        if not pools:
            self._logger.error(f'[{account.address}] Failed to fetch pools, exit...')
            return
        
        pools = self._remove_unsupported_pools(pools)
        if len(pools) == 0:
            self._logger.warning(f'[{account.address}] No supported pools found, exit...')
            return
        
        count_of_transactions = random.randint(self._settings.count_of_transactions[0], self._settings.count_of_transactions[1])
        self._logger.info(f'[{account.address}] Will execute {count_of_transactions} transactions')
        sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)   
        self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before adding liquidity')
        await asyncio.sleep(sleep_time)
        
        for i in range(count_of_transactions):
            pool = random.choice(pools)
            self._logger.info(f'[{account.address}] {i + 1}/{count_of_transactions} Adding liquidity to {pool.token0.symbol} - {pool.token1.symbol}')
            await self._add_liquidity(account_config, account, pool)
        
    async def _add_liquidity(self, account_config: AccountConfig, account: LocalAccount, pool: LiquidityPool) -> None:
        async with Web3Factory(account_config) as web3:
            for i in range(self._settings.retry_count):
                try:
                    self._logger.info(f'[{account.address}] Attempt {i + 1}/{self._settings.retry_count} Adding liquidity to {pool.token0.symbol} - {pool.token1.symbol}')
                    await self._try_add_liquidity(account_config, account, pool, web3)
                    break
                except Exception as e:
                    self._logger.error(f'[{account.address}] Attempt {i + 1}/{self._settings.retry_count} Failed to add liquidity to {pool.token0.symbol} - {pool.token1.symbol}: {e}')
                finally:
                    sleep_time = random.randint(MIN_SLEEP, MAX_SLEEP)   
                    self._logger.info(f'[{account.address}] Sleeping for {sleep_time} seconds before next attempt')
                    await asyncio.sleep(sleep_time)


    async def _try_add_liquidity(
        self, 
        account_config: AccountConfig, 
        account: LocalAccount, 
        pool: LiquidityPool, 
        web3: AsyncWeb3
    ) -> None:
        pm_contract = web3.eth.contract(
            address=web3.to_checksum_address(LIQUIDITY_ROUTER_ADDRESS), 
            abi=ABI['liquidity']
        )

        token0_balance, _ = await self._balance_checker.get_balance(
            account_config=account_config,
            token_address=pool.token0.address,
            account=account
        )

        token1_balance, _ = await self._balance_checker.get_balance(
            account_config=account_config,
            token_address=pool.token1.address,
            account=account
        )

        price = await self._get_pool_price(pool, web3)
        self._logger.info(f'[{account.address}] Fetched pool price: {price} {pool.token1.symbol}/{pool.token0.symbol}')

        percentage_of_balance = random.randint(self._settings.percentage_of_balance[0], self._settings.percentage_of_balance[1])
        token0_amount = int(token0_balance * percentage_of_balance / 100)
        token1_amount = min(int(token0_amount * price), token1_balance)
        token0_amount = int(token1_amount * (1 / price))

        if pool.token0.symbol != 'PHRS':
            await self._approval_service.approve_token(
                account_config=account_config,
                account=account,
                token_address=pool.token0.address,
                spender_address=pm_contract.address,
                amount=token0_amount
            )
        
        if pool.token1.symbol != 'PHRS':
            await self._approval_service.approve_token(
                account_config=account_config,
                account=account,
                token_address=pool.token1.address,
                spender_address=pm_contract.address,
                amount=token1_amount
            )

        mint_params = {
            'token0': web3.to_checksum_address(pool.token0.address),
            'token1': web3.to_checksum_address(pool.token1.address),
            'fee': pool.feeTier,
            'tickLower': -MAX_TICK,
            'tickUpper': MAX_TICK,
            'amount0Desired': token0_amount,
            'amount1Desired': token1_amount,
            'amount0Min': int(token0_amount * (1 - self._settings.slippage / 100)),
            'amount1Min': int(token1_amount * (1 - self._settings.slippage / 100)),
            'recipient': account.address,
            'deadline': await self._get_deadline(web3)
        }

        mint_data = pm_contract.encode_abi('mint', args=[mint_params])
        refund_data = pm_contract.encode_abi('refundETH', args=[])
        multicall_data = pm_contract.encode_abi('multicall', args=[[mint_data, refund_data]])

        value = 0
        if pool.token0.symbol == 'PHRS' or pool.token0.symbol == 'WPHRS':
            value = token0_amount
        elif pool.token1.symbol == 'PHRS' or pool.token1.symbol == 'WPHRS':
            value = token1_amount

        base_tx = {
            'from': account.address,
            'to': pm_contract.address,
            'data': multicall_data,
            'nonce': await web3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID,
            'value': value
        }

        await self._set_gas(base_tx, web3)

        signed_tx = account.sign_transaction(base_tx)
        tx_hash = await web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = await web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_url = ExplorerHelper.get_tx_url(tx_hash)

        if receipt['status'] == 1:
            result = decode(['uint128', 'uint256', 'uint256'], receipt['logs'][-1]['data'])
            _, provided_amount0, provided_amount1 = result
            provided_amount0 = provided_amount0 / (10 ** pool.token0.decimals)
            provided_amount1 = provided_amount1 / (10 ** pool.token1.decimals)
            self._logger.success(f'[{account.address}] ✅ Added liquidity: {provided_amount0:.2f} {pool.token0.symbol} and {provided_amount1:.2f} {pool.token1.symbol}: {tx_url}')
        else:
            self._logger.error(f'[{account.address}] ❌ Failed to add liquidity to {pool.token0.symbol} - {pool.token1.symbol}: {tx_url}')
            raise Exception('Transaction was not successful')


    async def _get_pool_price(self, pool: LiquidityPool, web3: AsyncWeb3) -> float:
        pool_contract = web3.eth.contract(
            address=web3.to_checksum_address(pool.id),
            abi=ABI['pool']
        )

        slot0 = await pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]
        price = (sqrt_price_x96 ** 2) / (1 << 192)
        price = price * (10 ** (pool.token0.decimals - pool.token1.decimals))
        return price
        
    
    async def _fetch_pools(self) -> list[LiquidityPool] | None:
        async with httpx.AsyncClient() as client:
            try:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                one_day_ago = today - timedelta(days=1)
                seven_days_ago = today - timedelta(days=7)
                
                data = {
                    "operationName": "PoolsBulkWithPriceChanges",
                    "query": FETCH_POOLS_QUERY,
                    "variables": {
                        "oneDayAgo": int(one_day_ago.timestamp()),
                        "sevenDaysAgo": int(seven_days_ago.timestamp())
                    }
                }
                response = await client.post(
                    'https://subgraph.zenithswap.xyz/testnet/subgraphs/name/dex-subgraph', 
                    json=data, 
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': '*/*',
                        'Origin': 'https://testnet.zenithfinance.xyz',
                        'Referer': 'https://testnet.zenithfinance.xyz/',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    },
                    follow_redirects=True)
                response.raise_for_status()
                
                data = response.json()
                if 'errors' in data and len(data['errors']) > 0:
                    raise Exception(data['errors'])
                
                pools = []
                for pool in data['data']['pools']:
                    token0 = LiquidityPoolToken(
                        address=pool['token0']['address'],
                        decimals=int(pool['token0']['decimals']),
                        derivedETH=float(pool['token0']['derivedETH']),
                        name=pool['token0']['name'],
                        symbol=pool['token0']['symbol']
                    )
                    token1 = LiquidityPoolToken(
                        address=pool['token1']['address'],
                        decimals=int(pool['token1']['decimals']),
                        derivedETH=float(pool['token1']['derivedETH']),
                        name=pool['token1']['name'],
                        symbol=pool['token1']['symbol']
                    )
                    
                    pool_obj = LiquidityPool(
                        id=pool['id'],
                        hash=pool['hash'],
                        feeTier=int(pool['feeTier']),
                        token0=token0,
                        token0Price=float(pool['token0Price']),
                        token1=token1,
                        token1Price=float(pool['token1Price']),
                        tick=int(pool['tick'])
                    )
                    pools.append(pool_obj)
                
                return pools
            except httpx.HTTPStatusError as e:
                self._logger.error(f'Error fetching pools: {e}')
                return None
            except Exception as e:
                self._logger.error(f'Error fetching pools: {e}')
                return None
            
    def _remove_unsupported_pools(self, pools: list[LiquidityPool]) -> list[LiquidityPool]:
        return [pool for pool in pools if pool.token0.symbol in TOKENS and pool.token1.symbol in TOKENS]
    
    async def _get_deadline(self, web3: AsyncWeb3) -> int:
        return (await web3.eth.get_block('latest'))['timestamp'] + 1200
    
    async def _set_gas(self, tx: dict, web3: AsyncWeb3) -> None:
        gas = await GasHelper.estimate_gas(web3, tx)
        gas_params = await GasHelper.get_gas_params(web3)

        tx.update({
            'gas': gas,
            **gas_params,
        })
    
    
    

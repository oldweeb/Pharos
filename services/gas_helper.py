from typing import Callable
from web3 import AsyncWeb3


class GasHelper:
    @staticmethod
    async def estimate_gas(web3: AsyncWeb3, tx: dict) -> int:
        """Estimate gas for a given transaction."""
        estimated_gas = await web3.eth.estimate_gas(tx)
        return int(estimated_gas * 1.1)
    
    @staticmethod
    async def estimate_gas_fn(fn: Callable, params: dict) -> int:
        estimated_gas = await fn.estimate_gas(params)
        return int(estimated_gas * 1.1)
    
    @staticmethod
    async def get_gas_params(web3: AsyncWeb3) -> dict[str, int]:
        """Get current gas parameters from the network."""
        latest_block = await web3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await web3.eth.max_priority_fee
        max_fee = base_fee + max_priority_fee
        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }

    @staticmethod
    async def get_gas_price(web3: AsyncWeb3) -> int:
        """Get current gas price from the network."""
        return await web3.eth.gas_price


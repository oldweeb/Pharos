from web3 import AsyncWeb3


class GasHelper:
    @staticmethod
    async def estimate_gas(cls, web3: AsyncWeb3, tx: dict) -> int:
        """Estimate gas for a given transaction."""
        estimated_gas = await web3.eth.estimate_gas(tx)
        return int(estimated_gas * 1.1)
    
    @staticmethod
    async def get_gas_params(self, web3: AsyncWeb3) -> dict[str, int]:
        """Get current gas parameters from the network."""
        latest_block = await self.web3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.web3.eth.max_priority_fee
        max_fee = base_fee + max_priority_fee
        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }

    @staticmethod
    async def get_gas_price(web3: AsyncWeb3) -> int:
        """Get current gas price from the network."""
        return await web3.eth.generate_gas_price()


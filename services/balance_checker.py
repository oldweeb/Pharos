from typing import Optional, Tuple
from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount
from eth_typing import Address, ChecksumAddress
from constants.chain import RPC_URL


class BalanceChecker:
    def __init__(self):
        """
        Initialize the BalanceChecker with an async Web3 instance.
        """
        self.web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))

    async def get_balance(self, token_address: str | Address | ChecksumAddress, account: LocalAccount) -> Tuple[int, int]:
        """
        Get the token balance for the specified account in wei and its decimals.
        
        Args:
            token_address (str | Address | ChecksumAddress): The token contract address
            account (LocalAccount): The account to check balance for
            
        Returns:
            Tuple[int, int]: A tuple containing (wei_balance, decimals)
        """
        # Convert token address to checksum address if it's a string
        if isinstance(token_address, str):
            token_address = self.web3.to_checksum_address(token_address)
            
        # ERC20 balanceOf and decimals functions ABI
        abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }, {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }]
        
        # Create contract instance
        contract = self.web3.eth.contract(address=token_address, abi=abi)
        
        # Get balance and decimals
        balance = await contract.functions.balanceOf(account.address).call()
        decimals = await contract.functions.decimals().call()
        
        return balance, decimals

    async def get_native_balance(self, account: LocalAccount) -> Tuple[int, int]:
        """
        Get the native token (PHRS) balance for the specified account in wei and its decimals.
        
        Args:
            account (LocalAccount): The account to check balance for
            
        Returns:
            Tuple[int, int]: A tuple containing (wei_balance, decimals) where decimals is always 18 for PHRS
        """
        balance = await self.web3.eth.get_balance(account.address)
        return balance, 18  # PHRS always has 18 decimals 
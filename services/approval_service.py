from loguru._logger import Logger
from dependency_injector.wiring import inject, Provide
from eth_account.signers.local import LocalAccount

from bootstrap.container import ApplicationContainer
from constants.abi import ABI
from constants.chain import CHAIN_ID
from models.configuration import AccountConfig
from services.explorer_helper import ExplorerHelper
from services.gas_helper import GasHelper
from services.web3_factory import Web3Factory

class ApprovalService:
    @inject
    def __init__(
        self, 
        logger: Logger = Provide[ApplicationContainer.logger],
    ):
        self._logger = logger
        
    async def approve_token(self, account_config: AccountConfig, account: LocalAccount, token_address: str, spender_address: str, amount: int) -> None:
        async with Web3Factory(account_config) as web3:  
            spender = web3.to_checksum_address(spender_address)
            token_address = web3.to_checksum_address(token_address)
            token_contract = web3.eth.contract(
                address=token_address, 
                abi=ABI['token']
            )
            if await self._is_approval_sufficient(account, token_contract, spender, amount):
                self._logger.info(f'[{account.address}] Approval for {token_address} to {spender_address} is sufficient')
                return
            
            approve_amount = 2 ** 256 - 1
            approve_function = token_contract.functions.approve(spender, approve_amount)
            transaction = {
                'from': account.address,
                'to': token_address,
                'data': approve_function._encode_transaction_data(),
                'chainId': CHAIN_ID,
                'type': 2,
                'nonce': await web3.eth.get_transaction_count(account.address, 'latest')
            }
            
            gas = await GasHelper.estimate_gas(web3, transaction)
            gas_params = await GasHelper.get_gas_params(web3)
            
            transaction.update({
                'gas': gas,
                **gas_params,
            })
            
            signed_tx = account.sign_transaction(transaction)
            tx_hash = await web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = await web3.eth.wait_for_transaction_receipt(tx_hash)
            
            tx_url = ExplorerHelper.get_tx_url(tx_hash)
            
            if receipt['status'] == 1:
                self._logger.success(f'[{account.address}] ✅ Approved {token_address} to {spender_address}: {tx_url}')
            else:
                self._logger.error(f'[{account.address}] ❌ Failed to approve {token_address} to {spender_address}: {tx_url}')
    
    async def _is_approval_sufficient(self, account, token_contract, spender_address, amount) -> bool:
        current_allowance = await token_contract.functions.allowance(account.address, spender_address).call()
        return current_allowance >= amount

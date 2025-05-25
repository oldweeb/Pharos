from hexbytes import HexBytes
from constants.chain import EXPLORER_URL


class ExplorerHelper:
    @staticmethod
    def get_tx_url(tx_hash: HexBytes) -> str:
        return f'{EXPLORER_URL}/tx/0x{tx_hash.hex()}'

from dataclasses import dataclass
from typing import Optional
from enum import Enum

@dataclass
class Account:
    private_key: str
    proxy: Optional[str]

@dataclass
class SwapsSettings:
    percentage_of_balance: list[int]
    count_of_swaps: list[int]
    swap_back_to_native: bool

@dataclass
class FaucetSettings:
    enabled: bool
    solvium_api_key: str

@dataclass
class LiquiditySettings:
    enabled: bool

class AccountsMode(Enum):
    SEQUENTIAL = 'sequential'
    PARALLEL = 'parallel'

@dataclass
class CheckinSettings:
    enabled: bool
    auth_key: str

@dataclass
class Settings:
    swaps: SwapsSettings
    faucet: FaucetSettings
    liquidity: LiquiditySettings
    checkin: CheckinSettings
    accounts_mode: AccountsMode = AccountsMode.SEQUENTIAL
    randomize_feature_order: bool = False

@dataclass
class Configuration:
    accounts: list[Account]
    settings: Settings


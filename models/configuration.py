from dataclasses import dataclass
from typing import Optional
from enum import Enum

@dataclass
class AccountConfig:
    private_key: str
    proxy: Optional[str]
    auth_key: str

@dataclass
class SwapsSettings:
    percentage_of_balance: list[int]
    count_of_swaps: list[int]
    swap_back_to_native: bool
    retry_count: int

@dataclass
class FaucetSettings:
    enabled: bool
    twocaptcha_key: str
    retry_captcha: int
    retry_count: int

@dataclass
class LiquiditySettings:
    enabled: bool

class AccountsMode(Enum):
    SEQUENTIAL = 'sequential'
    PARALLEL = 'parallel'

@dataclass
class CheckinSettings:
    enabled: bool
    retry_count: int
    pause_between_attemps: list[int]

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
    accounts: list[AccountConfig]
    settings: Settings


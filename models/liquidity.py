from dataclasses import dataclass

@dataclass
class LiquidityPoolToken:
    address: str
    decimals: int
    derivedETH: float
    name: str
    symbol: str

@dataclass
class LiquidityPool:
    id: str
    hash: str
    feeTier: int
    token0: LiquidityPoolToken
    token0Price: float
    token1: LiquidityPoolToken
    token1Price: float
    tick: int

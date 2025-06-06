ABI = {
    "token": [
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
    ],
    "weth": [
        {
            "constant": False,
            "inputs": [
                {"name": "guy", "type": "address"},
                {"name": "wad", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [{"name": "wad", "type": "uint256"}],
            "name": "withdraw",
            "outputs": [],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "dst", "type": "address"},
                {"name": "wad", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "payable": True,
            "stateMutability": "payable",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [
                {"name": "", "type": "address"},
                {"name": "", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "payable": True,
            "stateMutability": "payable",
            "type": "fallback"
        },
    ],
    "swap_router": [
        {
            "inputs": [{
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }],
            "name": "exactInputSingle",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [{
                "components": [
                    { "internalType": "bytes", "name": "path", "type": "bytes" },
                    { "internalType": "address", "name": "recipient", "type": "address" },
                    { "internalType": "uint256", "name": "amountIn", "type": "uint256" },
                    { "internalType": "uint256", "name": "deadline", "type": "uint256" },
                ],
                "internalType": "struct ISwapRouter.ExactInputParams",
                "name": "params",
                "type": "tuple"
            }],
            "name": "exactInput",
            "outputs": [
                { "internalType": "uint256", "name": "amountOut", "type": "uint256" }
            ],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256","name": "amountMinimum","type": "uint256"},
                {"internalType": "address","name": "recipient","type": "address"}
            ],
            "name": "unwrapWETH9",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "bytes[]", "name": "data", "type": "bytes[]"}
            ],
            "name": "multicall",
            "outputs": [{"internalType": "bytes[]", "name": "results", "type": "bytes[]"}],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "factory",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "factory": [
        {
            "inputs": [
                { "internalType": "address", "name": "tokenA", "type": "address" },
                { "internalType": "address", "name": "tokenB", "type": "address" },
                { "internalType": "uint24", "name": "fee", "type": "uint24" }
            ],
            "name": "getPool",
            "outputs": [
                { "internalType": "address", "name": "pool", "type": "address" }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "liquidity": [
        {
            "inputs": [
                { "internalType": "bytes[]", "name": "data", "type": "bytes[]" }
            ],
            "name": "multicall",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "components": [
                        { "internalType": "address", "name": "token0", "type": "address" },
                        { "internalType": "address", "name": "token1", "type": "address" },
                        { "internalType": "uint24",  "name": "fee", "type": "uint24" },
                        { "internalType": "int24",   "name": "tickLower", "type": "int24" },
                        { "internalType": "int24",   "name": "tickUpper", "type": "int24" },
                        { "internalType": "uint256", "name": "amount0Desired", "type": "uint256" },
                        { "internalType": "uint256", "name": "amount1Desired", "type": "uint256" },
                        { "internalType": "uint256", "name": "amount0Min", "type": "uint256" },
                        { "internalType": "uint256", "name": "amount1Min", "type": "uint256" },
                        { "internalType": "address", "name": "recipient", "type": "address" },
                        { "internalType": "uint256", "name": "deadline", "type": "uint256" }
                    ],
                    "internalType": "struct INonfungiblePositionManager.MintParams",
                    "name": "params",
                    "type": "tuple"
                }
            ],
            "name": "mint",
            "outputs": [
                { "internalType": "uint256", "name": "tokenId", "type": "uint256" },
                { "internalType": "uint128", "name": "liquidity", "type": "uint128" },
                { "internalType": "uint256", "name": "amount0", "type": "uint256" },
                { "internalType": "uint256", "name": "amount1", "type": "uint256" }
            ],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "refundETH",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ],
    "pool": [{
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }]
}
 
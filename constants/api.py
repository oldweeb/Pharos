CHECKIN_API_URL = 'https://api.pharosnetwork.xyz/sign/in?address={address}'
FAUCET_API_URL = 'https://api.pharosnetwork.xyz/faucet/daily?address={address}'
FAUCET_CHECK_API_URL = 'https://api.pharosnetwork.xyz/faucet/status?address={address}'

FETCH_POOLS_QUERY = """query PoolsBulkWithPriceChanges($oneDayAgo: Int!, $sevenDaysAgo: Int!) {
  pools(first: 20, orderBy: totalValueLockedUSD, orderDirection: desc) {
    id
    hash: id
    feeTier
    liquidity
    sqrtPrice
    tick
    token0 {
      id
      address: id
      symbol
      name
      decimals
      derivedETH
      __typename
    }
    token1 {
      id
      address: id
      symbol
      name
      decimals
      derivedETH
      __typename
    }
    token0Price
    token1Price
    volumeUSD
    txCount
    totalValueLockedToken0
    totalValueLockedToken1
    totalValueLockedUSD
    currentPrice: poolDayData(first: 1, orderBy: date, orderDirection: desc) {
      volumeUSD
      tvlUSD
      date
      __typename
    }
    oneDayAgoPrice: poolDayData(
      first: 1
      orderBy: date
      orderDirection: desc
      where: {date_lte: $oneDayAgo}
    ) {
      volumeUSD
      tvlUSD
      date
      __typename
    }
    sevenDaysAgoPrice: poolDayData(
      first: 1
      orderBy: date
      orderDirection: desc
      where: {date_lte: $sevenDaysAgo}
    ) {
      volumeUSD
      tvlUSD
      date
      __typename
    }
    __typename
  }
}"""
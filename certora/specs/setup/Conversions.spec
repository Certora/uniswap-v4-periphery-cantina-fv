using Conversions as Conv;

methods {
    function Conv.fromCurrency(Conversions.Currency) external returns (address) envfree;
    function Conv.toCurrency(address) external returns (Conversions.Currency) envfree;
    function Conv.poolKeyToId(Conversions.PoolKey) external returns (bytes32) envfree;
    function Conv.positionKey(address,int24,int24,bytes32) external returns (bytes32) envfree;
    function Conv.amount0(Conversions.BalanceDelta) external returns (int128) envfree;
    function Conv.amount1(Conversions.BalanceDelta) external returns (int128) envfree;
    function Conv.hashConfigElements(Conversions.Currency,Conversions.Currency,uint24,int24,address,int24,int24) external returns (bytes32) envfree;    
    function Conv.wrapToPoolId(bytes32) external returns (Conversions.PoolId) envfree;
}

function PoolKeyToId(Conversions.PoolKey key) returns bytes32 {
    return Conv.poolKeyToId(key);
}

function getPositionKey(address owner, int24 tickLower, int24 tickUpper, bytes32 salt) returns bytes32 {
    return Conv.positionKey(owner, tickLower, tickUpper, salt);
}
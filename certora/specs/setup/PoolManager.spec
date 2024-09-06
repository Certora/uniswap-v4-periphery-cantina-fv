/// This is a mock implementation of PoolManager in spec. It is suggested to only modify "*Conditions" functions by adding assumptions similar to `modifyLiquidityAmountsConditions`.

import "./Deltas.spec";
import "./PoolManagerBase.spec";
import "../ERC20/erc20cvl.spec";

methods {
    function TransientStateLibrary.currencyDelta(address manager, address user, Conversions.Currency currency) internal returns (int256) => getCurrencyDelta(manager, currency, user);

    function _.getPositionLiquidity(address manager, Conversions.PoolId poolId, bytes32 positionId) internal => 
        positionLiquidity(manager, poolId, positionId) expect uint128;

    function _.take(Conversions.Currency currency, address to, uint256 amount) external with (env e) =>
        takeMock(calledContract, currency, e.msg.sender, to, amount) expect void;

    function _.settle() external with (env e) =>
        settleMock(e, calledContract, e.msg.sender) expect uint256;

    function _.sync(Conversions.Currency currency) external with (env e) => syncMock(calledContract, currency) expect void;

    function _.modifyLiquidity(
        Conversions.PoolKey key,
        IPoolManager.ModifyLiquidityParams params,
        bytes 
    ) external with (env e) => 
        modifyLiquidityMock(e.msg.sender, key, params.tickLower, params.tickUpper, params.salt, params.liquidityDelta) expect (int256,int256);

    function _.swap(
        Conversions.PoolKey key, 
        IPoolManager.SwapParams params, 
        bytes
    ) external with (env e) =>
        swapMock(e.msg.sender, key, params.zeroForOne, params.amountSpecified, params.sqrtPriceLimitX96) expect int256;

    function _.clear(Conversions.Currency currency, uint256 amount) external with (env e) => clearMock(e,currency,amount) expect void;

    function _.initialize(Conversions.PoolKey key, uint160 sqrtPriceX96, bytes hookData) external with (env e) => initializeMock(e, key, sqrtPriceX96, hookData) expect int24;

    // We nondet this since _handleAction is no-op and summarizing unlock here would have no effect
    function _.unlock(bytes data) external => NONDET;
}

ghost address _syncedCurrency;
ghost uint256 _syncedReserves;

/// PoolManager pool-state ghosts:

/// The price tick for every pool.
ghost mapping(bytes32 => int24) poolTick;
/// The sqrtPriceX96 for every pool.
ghost mapping(bytes32 => uint160) poolSqrtPriceX96;
/// The total active liquidity per pool.
ghost mapping(bytes32 => uint128) liquidityPerPool;
/// The position liquidity for every (pool, position) pair.
ghost mapping(bytes32 => mapping(bytes32 => uint128)) positionLiquidityPerPool; 


function positionLiquidity(address manager, Conversions.PoolId poolId, bytes32 positionId) returns uint128 {
    assert manager == poolManager();
    bytes32 _id; require poolId == Conv.wrapToPoolId(_id);
    return positionLiquidityPerPool[_id][positionId];
}

function isActivePositionInPool(bytes32 poolId, int24 tickLower, int24 tickUpper) returns bool {
    return isActivePosition(poolTick[poolId], tickLower, tickUpper);
}

function swapMock(
    address swapper,
    Conversions.PoolKey key,
    bool zeroForOne,
    int256 amountSpecified,
    uint160 sqrtPriceLimitX96
) returns Conversions.BalanceDelta {
    /// Calculate hashed pool and position IDs.
    bytes32 poolId = PoolKeyToId(key);
    
    /// Declare random currency deltas for the caller and the provided pool hook address.
    int128 amount0_swapper;
    int128 amount1_swapper;
    int128 amount0_hook; // hook values are arbitrary, better assumtions can be made as needed
    int128 amount1_hook;
    int128 amount0_principal = require_int128(amount0_swapper + amount0_hook);
    int128 amount1_principal = require_int128(amount1_swapper + amount1_hook);

    /// Restrict the amounts based on provided swap details
    swapAmountsConditions(poolId, zeroForOne, amountSpecified, amount0_principal, amount1_principal);

    /// Update the pool state post-swap
    updatePoolStateOnSwap(poolId, zeroForOne, sqrtPriceLimitX96, amount0_principal, amount1_principal);

    /// Set currency deltas for msg.sender (position owner)
    setCurrencyDelta(key.currency0, swapper, amount0_swapper);
    setCurrencyDelta(key.currency1, swapper, amount1_swapper);
    /// Set currency delta for pool hook
    setCurrencyDelta(key.currency0, key.hooks, amount0_hook);
    setCurrencyDelta(key.currency1, key.hooks, amount1_hook);

    return amountsToBalanceDelta(amount0_swapper, amount1_swapper);
}

/// INSERT HERE A LIST OF REQUIREMENTS THAT CORRELATE THE TOKEN AMOUNTS FOR SWAPPING.
function swapAmountsConditions(
    bytes32 poolId, /// The poolId
    bool zeroForOne, /// swap to the left (true) or to the right (false)
    int256 x0,  /// amount specified (signed)
    int128 x0_swap, /// The currency0 swapped amount
    int128 x1_swap /// The currency1 swapped amount
) {
    // potential assumptions:
    /// direction of swapping: shouldn’t be getting both tokens and shouldn’t be giving both tokens

    require true;
}

/// CHANGE THE HAVOC STATEMENTS HERE THAT WILL DICTATE HOW THE POOL STATE CHANGES
function updatePoolStateOnSwap(
    bytes32 poolId, /// The poolId
    bool zeroForOne,/// swap to the left (true) or to the right (false)
    uint160 sqrtP_limit,  /// sqrtPriceLimitX96
    int128 x0_swap, /// The currency0 swapped amount
    int128 x1_swap /// The currency1 swapped amount 
) {
    /*
    Alternatively, one can declare a random variable and assign:
        int24 newTick;  poolTick[poolId] = newTick;
        uint160 newSqrtPrice;  poolTick[poolId] = newSqrtPrice;
        uint128 newLiquidity;  liquidityPerPool[poolId] = newLiquidity;
    */

    havoc poolTick assuming forall bytes32 poolIdA.
        (poolIdA != poolId => poolTick@new[poolIdA] == poolTick@old[poolIdA]);
    
    havoc poolSqrtPriceX96 assuming forall bytes32 poolIdA.
        (poolIdA != poolId => poolSqrtPriceX96@new[poolIdA] == poolSqrtPriceX96@old[poolIdA]);

    havoc liquidityPerPool assuming forall bytes32 poolIdA.
        (poolIdA != poolId => liquidityPerPool@new[poolIdA] == liquidityPerPool@old[poolIdA]);
}

function modifyLiquidityMock(
    address owner,
    Conversions.PoolKey key,
    int24 tickLower,
    int24 tickUpper,
    bytes32 salt,
    int256 delta
) returns (Conversions.BalanceDelta, Conversions.BalanceDelta) {
    /// Validate ticks
    require validTicks(tickLower, tickUpper);

    /// Ensure currencies are in order 
    require key.currency0 < key.currency1;

    /// Calculate hashed pool and position IDs.
    bytes32 poolId = PoolKeyToId(key);
    bytes32 positionId = getPositionKey(owner, tickLower, tickUpper, salt);

    /// Require pool is initialized
    require poolSqrtPriceX96[poolId] != 0;

    /// Update the position liquidity
    positionLiquidityPerPool[poolId][positionId] = require_uint128(
        positionLiquidityPerPool[poolId][positionId] + delta);

    /// Update the active pool liquidity
    if(isActivePositionInPool(poolId, tickLower, tickUpper)) {
        liquidityPerPool[poolId] = require_uint128(liquidityPerPool[poolId] + delta);
    }

    /// Declare random currency deltas for the caller and the provided pool hook address.
    int128 amount0_principal;
    int128 amount1_principal;
    int128 amount0_fees;
    int128 amount1_fees;
    int128 amount0_hook;
    int128 amount1_hook;
    /// Restrict the amounts based on provided liquidity delta:
    modifyLiquidityAmountsConditions(poolId, amount0_principal, amount1_principal, amount0_fees, amount1_fees, delta);

    int128 amount0_caller = require_int128(amount0_principal + amount0_fees);
    int128 amount1_caller = require_int128(amount1_principal + amount1_fees);

    // fee shouldn't cancel out whole principal
    require amount0_principal != 0 => amount0_caller != 0;
    require amount1_principal != 0 => amount1_caller != 0;

    /// Set currency deltas for msg.sender (position owner)
    setCurrencyDelta(key.currency0, owner, amount0_caller);
    setCurrencyDelta(key.currency1, owner, amount1_caller);
    /// Set currency delta for pool hook
    setCurrencyDelta(key.currency0, key.hooks, amount0_hook);
    setCurrencyDelta(key.currency1, key.hooks, amount1_hook);

    return (
        amountsToBalanceDelta(amount0_caller, amount1_caller),
        amountsToBalanceDelta(amount0_fees, amount1_fees)
    );
}

/// INSERT HERE A LIST OF REQUIREMENTS THAT CORRELATE THE TOKEN AMOUNTS WITH LIQUIDITY DELTA.
function modifyLiquidityAmountsConditions(
    bytes32 poolId, /// The poolId
    int128 x0_p,    /// The currency0 principal amount
    int128 x1_p,    /// The currency1 principal amount
    int128 x0_f,    /// The currency0 fee amount
    int128 x1_f,    /// The currency1 fee amount
    int256 dL       /// liquidity delta
) {
    require dL > 0 => x0_p < 0 && x1_p < 0;
    require dL < 0 => x0_p >= 0 && x1_p >= 0;
}

function settleMock(env e, address PoolManager, address recipient) returns uint256 {
    uint256 paid;
    if (_syncedCurrency == 0) {
        paid = e.msg.value;
    } else {
        paid = require_uint256(balanceOfCVL(_syncedCurrency, PoolManager) - _syncedReserves);
    }
    setCurrencyDelta(Conv.toCurrency(_syncedCurrency), recipient, require_int128(paid));

    _syncedCurrency = 0;    
    return paid;
}

function takeMock(address PoolManager, Conversions.Currency currency, address caller, address to, uint256 amount) {
    require (caller != PoolManager); // The PoolManager cannot call itself.
    setCurrencyDelta(currency, caller, require_int128(-require_uint128(amount)));
    transferCVL(Conv.fromCurrency(currency), PoolManager, to, amount);
}

function syncMock(address PoolManager, Conversions.Currency currency) {
    require _syncedCurrency == 0;
    address token = Conv.fromCurrency(currency);
    if(token == NATIVE()) return;
    _syncedReserves = balanceOfCVL(token, PoolManager);
    _syncedCurrency = token;
}

function clearMock(env e, Conversions.Currency currency, uint256 amount) {
    int256 current = getCurrencyDeltaExt(currency, e.msg.sender);

    require current == require_int256(amount);

    setCurrencyDelta(currency, e.msg.sender, require_int128(-require_uint128(amount)));
}

function initializeMock(env e, Conversions.PoolKey key, uint160 sqrtPriceX96, bytes hookData) returns int24 {
    require key.currency0 < key.currency1;
    
    bytes32 poolId = PoolKeyToId(key);
    
    havoc poolTick assuming forall bytes32 poolIdA.
        (poolIdA != poolId => poolTick@new[poolIdA] == poolTick@old[poolIdA]);
    
    havoc poolSqrtPriceX96 assuming forall bytes32 poolIdA.
        (poolIdA != poolId => poolSqrtPriceX96@new[poolIdA] == poolSqrtPriceX96@old[poolIdA]);

    // Only assuming min and max bounds
    require poolSqrtPriceX96[poolId] >= 4295128739 && poolSqrtPriceX96[poolId] < 1461446703485210103287273052203988822378723970342;
    require -887272 <= poolTick[poolId] && poolTick[poolId] <= 887272;  
    require liquidityPerPool[poolId] == 0;

    return poolTick[poolId];
}
/// This file proves properties about PoolManager which can be assumed in the mock spec. 

import "./Deltas.spec";
import "./Conversions.spec";
import "./PoolManagerBase.spec";
import "./PoolManagerAuxiliary.spec";
import "../ERC20/erc20cvl.spec";

using PoolManager as PM;
using PoolGetters as PoolGetters;

methods {
    function CurrencyDelta.applyDelta(PoolManager.Currency currency, address user, int128 delta) internal returns (int256,int256) => setCurrencyDelta(currency, user, delta);
    function CurrencyDelta.getDelta(PoolManager.Currency currency, address user) internal returns int256 => getCurrencyDelta(calledContract, currency, user);
    function _.currencyDelta(address manager, address user, Conversions.Currency currency) internal => getCurrencyDelta(manager, currency, user) expect int256;

    function PoolGetters.getTick(Conversions.PoolId) external returns (int24) envfree;
    function PoolGetters.getSyncedCurrency() external returns (PoolManager.Currency) envfree;
    function PoolGetters.getSyncedReserves() external returns (uint256) envfree;
}

function getPoolManager() returns address {
    return currentContract;
}

rule modifyLiquidity_liquidity_test()
{
    /// modifyLiquidity params:
    env e;
    PoolManager.PoolKey key;
    IPoolManager.ModifyLiquidityParams params;
    bytes data;    

    /// Calculate hashed pool and position IDs.
    Conversions.PoolId poolId = Conv.wrapToPoolId(PoolKeyToId(key));
    bytes32 positionId = getPositionKey(e.msg.sender, params.tickLower, params.tickUpper, params.salt);  
    bool isActive = isActivePosition(PoolGetters.getTick(poolId), params.tickLower, params.tickUpper);  

    /// Independent pools and position IDs.
    Conversions.PoolId poolIdA; require poolId != poolIdA;
    bytes32 positionIdA; require positionId != positionIdA;

    uint128 activeLiquidity_pre = getActiveLiquidity(poolId);
    uint128 activeLiquidity_other_pre = getActiveLiquidity(poolIdA);
    uint128 positionLiquidity_pre = getPositionLiquidityDirect(poolId, positionId);
    uint128 positionLiquidity_other_pre = getPositionLiquidityDirect(poolId, positionIdA);
    uint128 positionLiquidity_other_pool_pre = getPositionLiquidityDirect(poolIdA, poolIdA);
        
        PoolManager.BalanceDelta callerDelta;
        PoolManager.BalanceDelta feesAccrued;
        callerDelta, feesAccrued = modifyLiquidity(e, key, params, data);

    uint128 activeLiquidity_post = getActiveLiquidity(poolId);
    uint128 activeLiquidity_other_post = getActiveLiquidity(poolIdA);
    uint128 positionLiquidity_post = getPositionLiquidityDirect(poolId, positionId);
    uint128 positionLiquidity_other_post = getPositionLiquidityDirect(poolId, positionIdA);
    uint128 positionLiquidity_other_pool_post = getPositionLiquidityDirect(poolIdA, poolIdA);
    
    assert isActive => activeLiquidity_post - activeLiquidity_pre == params.liquidityDelta;
    assert !isActive => activeLiquidity_post == activeLiquidity_pre;
    assert activeLiquidity_other_post == activeLiquidity_other_pre;
    assert positionLiquidity_post - positionLiquidity_pre == params.liquidityDelta;
    assert positionLiquidity_other_post == positionLiquidity_other_pre;
    assert positionLiquidity_other_pool_post == positionLiquidity_other_pool_pre;
}

rule modifyLiquidity_deltas_test() 
{
    /// modifyLiquidity params:
    env e;
    PoolManager.PoolKey key;
    IPoolManager.ModifyLiquidityParams params;
    bytes data;

    /// Independent currency and account:
    PoolManager.Currency currency2;
    require currency2 != key.currency0 && currency2 != key.currency1;
    address account;
    require account != e.msg.sender && account != key.hooks;

    /// Other account deltas:
    int256 delta0_other_pre = getCurrencyDelta(PM, key.currency0, account);
    int256 delta1_other_pre = getCurrencyDelta(PM, key.currency1, account);
    int256 delta2_other_pre = getCurrencyDelta(PM, currency2, account);
    /// msg.sender deltas:
    int256 delta0_sender_pre = getCurrencyDelta(PM, key.currency0, e.msg.sender);
    int256 delta1_sender_pre = getCurrencyDelta(PM, key.currency1, e.msg.sender);
    int256 delta2_sender_pre = getCurrencyDelta(PM, currency2, e.msg.sender);
    /// hooks deltas:
    int256 delta0_hooks_pre = getCurrencyDelta(PM, key.currency0, key.hooks);
    int256 delta1_hooks_pre = getCurrencyDelta(PM, key.currency1, key.hooks);
    int256 delta2_hooks_pre = getCurrencyDelta(PM, currency2, key.hooks);

        PoolManager.BalanceDelta callerDelta;
        PoolManager.BalanceDelta feesAccrued;
        callerDelta, feesAccrued = modifyLiquidity(e, key, params, data);

    /// Other account deltas:
    int256 delta0_other_post = getCurrencyDelta(PM, key.currency0, account);
    int256 delta1_other_post = getCurrencyDelta(PM, key.currency1, account);
    int256 delta2_other_post = getCurrencyDelta(PM, currency2, account);
    /// msg.sender deltas:
    int256 delta0_sender_post = getCurrencyDelta(PM, key.currency0, e.msg.sender);
    int256 delta1_sender_post = getCurrencyDelta(PM, key.currency1, e.msg.sender);
    int256 delta2_sender_post = getCurrencyDelta(PM, currency2, e.msg.sender);
    /// hooks deltas:
    int256 delta0_hooks_post = getCurrencyDelta(PM, key.currency0, key.hooks);
    int256 delta1_hooks_post = getCurrencyDelta(PM, key.currency1, key.hooks);
    int256 delta2_hooks_post = getCurrencyDelta(PM, currency2, key.hooks);

    assert validTicks(params.tickLower, params.tickUpper);

    /// Other account deltas:
    assert delta0_other_pre == delta0_other_post;
    assert delta1_other_pre == delta1_other_post;
    assert delta2_other_pre == delta2_other_post;

    /// msg.sender deltas:
    assert delta0_sender_post - delta0_sender_pre == Conv.amount0(callerDelta);
    assert delta1_sender_post - delta1_sender_pre == Conv.amount1(callerDelta);
    assert delta2_sender_post == delta2_sender_pre;

    /// Hook deltas:
    satisfy key.hooks != e.msg.sender && delta0_hooks_post - delta0_hooks_pre != 0;
    satisfy key.hooks != e.msg.sender && delta1_hooks_post - delta1_hooks_pre != 0;
    assert delta2_hooks_post == delta2_hooks_pre;
}

rule take_test(address account, address token) {
    env e;
    PoolManager.Currency currency;
    address to;
    uint256 amount;

    uint256 balance_pre = balanceOfCVL(token, account);
    int256 delta_pre = getCurrencyDelta(currentContract, Conv.toCurrency(token), account);
        take(e, currency, to, amount);
    uint256 balance_post = balanceOfCVL(token, account);
    int256 delta_post = getCurrencyDelta(currentContract, Conv.toCurrency(token), account);

    if(Conv.toCurrency(token) == currency) {
        if(account == to) {
            assert to != PM => balance_post - balance_pre == amount;
            assert to == PM => balance_post == balance_pre;
            assert delta_pre - delta_post == amount;
        } else {
            assert account == PM => balance_pre - balance_post == amount;
            assert account != PM => balance_post == balance_pre;
            assert delta_pre == delta_post;
        }
    } else {
        assert balance_post == balance_pre;
        assert delta_pre == delta_post;
    }
}

rule settle_test(address account, address token) {
    env e;
    require e.msg.sender != PM; /// PoolManager doesn't call itself.
    PoolManager.Currency currency = PoolGetters.getSyncedCurrency();
    address to = e.msg.sender;
    uint256 synchedBalancePM = balanceOfCVL(Conv.fromCurrency(currency), PM);
    uint256 amount;

    if(Conv.fromCurrency(currency) == NATIVE()) {
        require amount == e.msg.value;
    } else {
        require amount == require_uint256(synchedBalancePM - PoolGetters.getSyncedReserves());
    }
    
    uint256 balance_pre = balanceOfCVL(token, account);
    int256 delta_pre = getCurrencyDelta(currentContract, Conv.toCurrency(token), account);
        uint256 paid = settle(e);
    uint256 balance_post = balanceOfCVL(token, account);
    int256 delta_post = getCurrencyDelta(currentContract, Conv.toCurrency(token), account);

    assert paid == amount;
    if(Conv.toCurrency(token) == currency) {
        if(account == to) {
            assert delta_post - delta_pre == paid;
        } else {
            assert delta_pre == delta_post;
        }
    } else {
        assert delta_pre == delta_post;
    }
    
    if(token == NATIVE() && Conv.fromCurrency(currency) == NATIVE()) {
        assert account == PM => balance_post - balance_pre == paid;
        assert account == e.msg.sender => balance_pre - balance_post == paid;
        assert account != PM && account != e.msg.sender => balance_post == balance_pre;
    } else {
        assert balance_post == balance_pre;
    }
    assert PoolGetters.getSyncedCurrency() == Conv.toCurrency(NATIVE());
}
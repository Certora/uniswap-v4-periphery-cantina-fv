# **Uniswap v4 Audit Competition**

## Table of Contents

- [**Overview**](#overview)
- [**Mutations**](#mutations)
  - [**DeltaResolver**](#deltaresolver)
  - [**PositionManager**](#positionmanager)
  - [**V4Router**](#v4router)
- [**Notable Properties**](#notable-properties)
  - [**PositionManager**](#positionmanager-1)
  - [**DeltaResolver**](#deltaresolver-1)
  - [**V4Router**](#v4router-1)
- [**Disclaimer**](#disclaimer)

# Overview

This report summarizes the findings from the Uniswap v4 audit competition, focusing on formal verification of key contracts. The competition tested the resilience of verified properties against introduced mutations (high-severity bugs), providing insights into the effectiveness of the formal verification approach.

# Mutations

## DeltaResolver

**DeltaResolver_0**
- Change: Removed "-" before `_amount` in `_getFullDebt`, returning an amount with the wrong sign
- Breaking properties:
  - Don't pay too much debt (delta vs balance change)
  - PosM should take exact amount as delta, not more or less

**DeltaResolver_1**
- Change: Failed to call `sync` in `_settle`
- Breaking property:
  - If currency is not set, debt can't be paid (defaults to native and checks msg.value for repayment amount)
  - Debt must be payable, _settle should decrease debt/delta

## PositionManager

**PositionManager_0**
- Change: Transfer ether instead of `currency` in `_sweep`
- Breaking property: Sweep integrity, should not affect a 3rd currency

**PositionManager_1**
- Change: Sum liquidityDelta and feesAccrued in `_increase` instead of subtracting when calling `validateMaxIn`
- Breaking property: MaxIn validation is miscalculated, allowing more than max to be deposited

**PositionManager_2**
- Change: Never notify subscribers in `transferFrom` and only transfer if position has subscriber
- Breaking property: TransferFrom integrity

**PositionManager_3**
- Change: Failed to burn the token in `_burn`
- Breaking property: Balance should decrease on burn

**PositionManager_4**
- Change: In `_clearOrTake`, call `clear` when delta is greater than amountMax instead of `take`
- Breaking property: Delta decreases by more than min amount must mean user gets tokens

**PositionManager_5**
- Change: Failed to increment tokenId in `_mint`
- Breaking property: TokenId monotonic

**PositionManager_6**
- Change: Take `currency0` twice in `_takePair`
- Breaking property: TakePair integrity

**PositionManager_7**
- Change: Switch `liquidityDelta` and `feesAccrued` in `_modifyLiquidity`
- Breaking property: Should break many properties

**PositionManager_8**
- Change: Replace `-(liquidity.toInt256())` with 0 in `_decrease`, passing in 0 as liquidityDelta
- Breaking property: Decreasing liquidity must result in a change delta

## V4Router

**V4Router_0**
- Change: Replace `currencyIn` with `default0` in `_swapExactInput`
- Breaking property: Loop doesn't actually execute

**V4Router_1**
- Change: Remove `V4TooMuchRequested` revert in `_swapExactOutput`
- Breaking property: Passed in currency is not the one that is swapped

**V4Router_2**
- Change: Switch `params.poolKey.currency1` and `params.poolKey.currency0` in `_swapExactOutputSingle`
- Breaking property: The full debt of the wrong currency is returned

**V4Router_3**
- Change: Make `_swap` always return 0
- Breaking property: `_swap` always returns 0, causing _swapExactInputSingle and other swap callers to revert in most acceptable cases

[Previous sections remain the same until Notable Properties]

# Notable Properties

## PositionManager

### TokenId Monotonicity and Slippage Protection
*Author: 0x00ffDa*

```solidity
rule mintSlippageOk(env e) {
    PositionManagerHarness.PoolKey poolKey;
    uint256 liquidity; uint128 amount0Max; uint128 amount1Max; bytes hookData;
    uint256 tokenId = nextTokenId();
    require tokenId < max_uint256;
    
    ghostFeesDelta0 = 0; ghostFeesDelta1 = 0;
    
    int256 delta0Before = getCurrencyDeltaExt(poolKey.currency0, currentContract);
    int256 delta1Before = getCurrencyDeltaExt(poolKey.currency1, currentContract);

    mintPosition(e, poolKey, _/*tickLower*/, _/*tickLower*/, liquidity, amount0Max, amount1Max, _, hookData);

    int256 delta0After = getCurrencyDeltaExt(poolKey.currency0, currentContract);
    int256 delta1After = getCurrencyDeltaExt(poolKey.currency1, currentContract);

    assert delta0Before - delta0After >= 0;
    assert delta0Before - delta0After <= amount0Max;
    assert delta1Before - delta1After >= 0;
    assert delta1Before - delta1After <= amount1Max;
    assert nextTokenId() == tokenId + 1;
}
```

### Clear or Take Logic
*Author: 0x00ffDa*

```solidity
rule clearOrTake(env e, Conversions.Currency currency, uint256 limit) {
    address token = Conv.fromCurrency(currency);
    int256 amount = ghostCurrencyDelta[currentContract][token];
    address recipient = e.msg.sender;
    uint256 recipBalanceBefore = balanceOfCVL(token, recipient);
    address poolMan = poolManager();
    uint256 PmBalanceBefore = balanceOfCVL(token, poolMan);
    require recipient != poolMan;

    address otherUser;
    require otherUser != poolMan && otherUser != recipient;
    uint256 otherBalanceBefore = balanceOfCVL(token, otherUser);

    address otherToken;
    require otherToken != token;
    address anyUser;
    uint256 anyOtherTokenBalanceBefore = balanceOfCVL(otherToken, anyUser);

    clearOrTake(e, currency, limit);

    if (amount > limit) {
        // take
        assert balanceOfCVL(token, recipient) == recipBalanceBefore + amount;
        assert balanceOfCVL(token, poolMan) == PmBalanceBefore - amount;
    }
    assert ghostCurrencyDelta[currentContract][token] == 0;
    assert balanceOfCVL(token, otherUser) == otherBalanceBefore;
    assert balanceOfCVL(otherToken, anyUser) == anyOtherTokenBalanceBefore;
}
```

### Increase Liquidity Integrity
*Author: 0x00ffDa*

```solidity
rule increaseLiquidity(env e, uint256 tokenId, uint256 increase, uint128 amount0Max, uint128 amount1Max, bytes hookData) {
    ghostNotifiedOfLiquidityMod = false;

    PositionManagerHarness.PoolKey poolKey; 
    PositionManagerHarness.PositionInfo info;
    (poolKey, info) = getPoolAndPositionInfo(tokenId);
    uint128 liquidityBefore = getLiquidity(tokenId, poolKey, info);

    int256 delta0Before = getCurrencyDeltaExt(poolKey.currency0, currentContract);
    int256 delta1Before = getCurrencyDeltaExt(poolKey.currency1, currentContract);

    uint256 otherTokenId;
    require otherTokenId != tokenId;
    PositionManagerHarness.PoolKey otherPoolKey; 
    PositionManagerHarness.PositionInfo otherInfo;
    (otherPoolKey, otherInfo) = getPoolAndPositionInfo(otherTokenId);
    uint128 otherLiquidityBefore = getLiquidity(otherTokenId, otherPoolKey, otherInfo);

    increaseLiquidity(e, tokenId, increase, amount0Max, amount1Max, hookData);

    assert getLiquidity(tokenId, poolKey, info) == liquidityBefore + increase;

    int256 delta0After = getCurrencyDeltaExt(poolKey.currency0, currentContract);
    int256 delta1After = getCurrencyDeltaExt(poolKey.currency1, currentContract);
    if (increase != 0) {
        validateOwed(delta0Before - (delta0After - ghostFeesDelta0), amount0Max);
        validateOwed(delta1Before - (delta1After - ghostFeesDelta1), amount1Max);
    }
    else {
        mathint fees0 = delta0After - delta0Before;
        mathint fees1 = delta1After - delta1Before;
        assert fees0 == ghostFeesDelta0 && fees1 == ghostFeesDelta1;
    }
    assert decodeHasSubscriber(info) => ghostNotifiedOfLiquidityMod;
    assert getLiquidity(otherTokenId, otherPoolKey, otherInfo) == otherLiquidityBefore;
}
```

### Increase Liquidity Slippage Protection
*Author: BenRai1*

```solidity
rule B10increaseLiquidityHasSlippageProtection(env e){ 
    uint256 tokenId;
    uint256 liquidity;
    uint128 amount0Max;
    uint128 amount1Max;
    bytes hookData;
    Conversions.PoolKey poolKey;
    Conversions.PositionInfo positionInfo;
    (poolKey, positionInfo) = getPoolAndPositionInfo(tokenId);
    require(poolKey.hooks != currentContract);

    Conversions.Currency currency0 = poolKey.currency0;
    Conversions.Currency currency1 = poolKey.currency1;
    int128 deltaCurrency0Before = getCurrencyDeltaExt(currency0, currentContract);
    int128 deltaCurrency1Before = getCurrencyDeltaExt(currency1, currentContract);	
    require(deltaCurrency0Before == 0 && deltaCurrency1Before == 0);
    int128 deltaFeesCurrency0Before = feesDelta[currency0];
    int128 deltaFeesCurrency1Before = feesDelta[currency1];
    require(deltaFeesCurrency0Before == 0 && deltaFeesCurrency1Before == 0);

    increaseLiquidityHarness(e, tokenId, liquidity, amount0Max, amount1Max, hookData);

    int deltaCurrency0After = getCurrencyDeltaExt(currency0, currentContract);
    int256 deltaCurrency1After = getCurrencyDeltaExt(currency1, currentContract);
    require(deltaCurrency0After > -2^(128/2) && deltaCurrency0After > -2^(128/2));
    int128 deltaFeesCurrency0After = feesDelta[currency0];
    int128 deltaFeesCurrency1After = feesDelta[currency1];
    
    assert(deltaCurrency0Before != deltaCurrency0After - deltaFeesCurrency0After => 
           amount0Max >= -(deltaCurrency0After - deltaFeesCurrency0After));
    assert(deltaCurrency1Before != deltaCurrency1After - deltaFeesCurrency1After => 
           amount1Max >= -(deltaCurrency1After- deltaFeesCurrency1After));    
}
```

### Different Tokens Have Different Position IDs
*Author: BenRai1*

```solidity
invariant differentTokensHaveDifferentPositionIds(uint256 tokenId1, uint256 tokenId2)
    positionInfo(tokenId1) != positionInfo(tokenId2) || positionInfo(tokenId1) == 0 || positionInfo(tokenId2) == 0
    filtered {
        f -> f.selector != sig:subscribe(uint256,address,bytes).selector
        && f.selector != sig:unsubscribe(uint256).selector
        && f.selector != sig:_setUnsubscribedHarness(uint256).selector
        && f.selector != sig:_setSubscribedHarness(uint256).selector
    }
    {
        preserved {
            require(tokenId1 != 0);
            require(tokenId2 != 0);
            require(tokenId1 < nextTokenId());
            require(tokenId2 < nextTokenId());
            require positionInfo(tokenId1) != 0;
            require positionInfo(tokenId2) != 0;
            requireInvariant R0unmintedTokensDoNotHavePositionInfo(tokenId1);
            requireInvariant R0unmintedTokensDoNotHavePositionInfo(tokenId2);
            requireInvariant R3ownerOfUnmitedTokensIsAlways0(tokenId1);
            requireInvariant R3ownerOfUnmitedTokensIsAlways0(tokenId2);
        }
    }
```

## DeltaResolver

### Settle and Take Monotonicity
*Author: jraynaldi31*

```solidity
rule settle_take_monoton(
    env e,
    Conversions.Currency currency,
    uint256 amount
) {
    require poolManager() != currentContract && poolManager() != e.msg.sender;
    int256 deltaBefore = getCurrencyDeltaExt(currency, currentContract);
    require amount != 0;

    uint256 realSettleAmount = getSettleAmount(amount, currency);
    uint256 realTakeAmount = getTakeAmount(amount, currency);
    require realSettleAmount == realTakeAmount;

    take(e, currency, _ , amount);
    settle(e, currency, amount, _ );

    assert deltaBefore == getCurrencyDeltaExt(currency, currentContract);
}
```

### Pool Manager Balance Delta Correlation
*Author: jraynaldi31*

```solidity
rule poolManagerBalance_delta_correlation(
    env e,
    method f,
    calldataarg args,
    Conversions.Currency currency
) filtered {f-> f.contract == currentContract} {
    require poolManager() != currentContract;
    uint256 balanceBefore = balanceOfCVL(Conv.fromCurrency(currency), poolManager());
    int256 deltaBefore = getCurrencyDeltaExt(currency, currentContract);

    if (f.selector == sig:sweep(Conversions.Currency,address).selector) {
        address to;
        require poolManager() != to;
        require poolManager() != e.msg.sender;
        sweep(e, currency, to);
    } else {
        f(e,args);
    }

    uint256 balanceAfter = balanceOfCVL(Conv.fromCurrency(currency), poolManager());
    int256 deltaAfter = getCurrencyDeltaExt(currency, currentContract);
    assert balanceBefore > balanceAfter => deltaBefore > deltaAfter;
    assert balanceBefore < balanceAfter => deltaBefore < deltaAfter;
}
```

## V4Router

### Contract Lock Status
*Author: 0x00ffDa*

```solidity
invariant currentContractUnlocked()
    msgSender() == 0;
```

### Multiple Swaps Possibility
*Author: 0x00ffDa*

```solidity
rule twoSwapsPossible() {
    bool singleHopOnly;
    env e1;
    bool firstSwapExactIn;
    doAnySwap(e1, singleHopOnly, _, _, firstSwapExactIn, _, _);

    env e2;
    require e2.msg.sender == e1.msg.sender;
    bool secondSwapExactIn;
    doAnySwap(e2, singleHopOnly, _, _, secondSwapExactIn, _, _);

    satisfy singleHopOnly && firstSwapExactIn && secondSwapExactIn;
    satisfy singleHopOnly && firstSwapExactIn && !secondSwapExactIn;
    satisfy singleHopOnly && !firstSwapExactIn && secondSwapExactIn;
    satisfy singleHopOnly && !firstSwapExactIn && !secondSwapExactIn;
    satisfy !singleHopOnly;
}
```

### Exact Input Delta Integrity
*Author: BenRai1*

```solidity
rule _swapExactInputDoesNotChangeDeltaOfCurrency2(env e) {
    IV4Router.ExactInputParams params;
    uint128 initialAmountIn = params.amountIn;
    Conversions.PoolKey poolKey;
    bool zeroForOne;
    (poolKey, zeroForOne) = getPoolAndSwapDirectionDirectHarness(params.path[0], params.currencyIn);
    uint256 amountIn = mapAmountInHarness(initialAmountIn, poolKey, zeroForOne);
    IV4Router.PathKey[] pathKey = params.path;
    require(pathKey.length == 2);
    Conversions.Currency currencyIn = params.currencyIn;
    Conversions.Currency currency2 = pathKey[0].intermediateCurrency;
    Conversions.Currency currencyOut = pathKey[1].intermediateCurrency;
    require(currencyIn != currency2 && currency2 != currencyOut && currencyIn != currencyOut);
    address hooks1 = pathKey[0].hooks;
    address hooks2 = pathKey[1].hooks;
    require(hooks1 != currentContract && hooks2 != currentContract);

    int256 deltaCurrency2Before = getCurrencyDeltaExt(currency2, currentContract);

    swapExactInputHarness(e, params);

    int256 deltaCurrency2After = getCurrencyDeltaExt(currency2, currentContract);

    assert(deltaCurrency2After == deltaCurrency2Before);
}
```

### Swap Direction Integrity
*Author: jraynaldi31*

```solidity
rule zeroForOne_integrity(
    env e,
    method f,
    IV4Router.ExactInputSingleParams inSingleParams,
    IV4Router.ExactOutputSingleParams outSingleParams,
    address account
) {
    bool zeroForOneCVL;
    Conversions.Currency  currency0; Conversions.Currency currency1;
    require inSingleParams.zeroForOne == outSingleParams.zeroForOne;
    require zeroForOneCVL == inSingleParams.zeroForOne;
    require inSingleParams.poolKey.currency0 == outSingleParams.poolKey.currency0;
    require inSingleParams.poolKey.currency0 == currency0;
    require inSingleParams.poolKey.currency1 == outSingleParams.poolKey.currency1;
    require inSingleParams.poolKey.currency1 == currency1;


    int256 delta0Before = getCurrencyDeltaExt(currency0, account);
    int256 delta1Before = getCurrencyDeltaExt(currency1, account);

    if (f.selector == sig:swapExactInSingle(IV4Router.ExactInputSingleParams).selector) {
        swapExactInSingle(e, inSingleParams);
    } else if (f.selector == sig:swapExactOutSingle(IV4Router.ExactOutputSingleParams).selector) {
        swapExactOutSingle(e, outSingleParams);
    }

    int256 delta0After = getCurrencyDeltaExt(currency0, account);
    int256 delta1After = getCurrencyDeltaExt(currency1, account);

    assert delta0Before > delta0After => zeroForOneCVL;
    assert delta1Before > delta1After => !zeroForOneCVL;
}
```

# Disclaimer

This report does not guarantee complete security of the audited contracts. Continuous review and comprehensive testing are advised before deploying any smart contracts.

The formal verification competition demonstrates the effectiveness of mathematical validation in identifying potential vulnerabilities and ensuring contract correctness. However, users should still exercise caution and conduct their own due diligence.

Smart contract software should be used at the sole risk and responsibility of users. Neither the authors of this report nor the competition organizers provide any warranty regarding the security of these contracts.
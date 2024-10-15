Potential properties that are broken by the mutation, useful to understand other what other similar bugs the mutation catching rule would catch

**DeltaResolver**

DeltaResolver_0

    code change:
    * remove "-" before `_amount` in `_getFullDebt`, returning an amount with the wrong sign

    breaking property:
    * don't pay too much debt (delta vs balance change)
    * PosM should take exact amount as delta, not more or less

DeltaResolver_1
    
    code change:
    * fail to call `sync` in `_settle`

    breaking property:
    * if currency is not set, debt can't be paid (defaults to native and checks msg.value for repayment amount)Debt must be payable, _settle should decrease debt/delta

**PositionManager**

PositionManager_0

    code change:
    * transfer ether instead of `currency` in `_sweep`

    breaking property:
    * sweep integrity, should not effect a 3rd currency

PositionManager_1

    code change:
    * sum liquidityDelta and feesAccrued in `_increase` instead of subtracting when calling `validateMaxIn`

    breaking property:
    * maxIn validation is mis calculated, allowing more than max to be deposited

PositionManager_2

    code change:
    * never notify subscribers in `transferFrom` and only transfer if position has subscriber

    breaking property:
    * transferFrom integrity

PositionManager_3

    code change:
    * fail to burn the token in `_burn`

    breaking property:
    * balance should decrease on burn

PositionManager_4

    code change:
    * in `_clearOrTake`, call `clear` when delta is greater than amountMax instead of `take`

    breaking property:
    * delta decreases by more than min amount must mean user gets tokens? unsure because mock poolM

PositionManager_5

    code change:
    * fail to increment tokenId in `_mint`

    breaking property:
    * tokenId monotonic

PositionManager_6

    code change:
    * take `currency0` twice in `_takePair`

    breaking property:
    * takePair integrity

PositionManager_7

    code change:
    * switch `liquidityDelta` and `feesAccrued` in `_modifyLiquidity`

    breaking property:
    * should break many properties

PositionManager_8

    code change:
    * replace `-(liquidity.toInt256())` with 0 in `_decrease`, passing in 0 as liquidityDelta

    breaking property:
    * decreasing liquidity must result in a change delta

**V4Router**

V4Router_0

    code change:
    * replace `currencyIn` with `default0` in `_swapExactInput`

    breaking property:
    * loop doesn't actually execute, not super interesting, better to have something else

V4Router_1

    code change:
    * remove `V4TooMuchRequested` revert in `_swapExactOutput`

    breaking property:
    * Passed in currency is not the one that is swapped

V4Router_2

    code change:
    * switch `params.poolKey.currency1` and `params.poolKey.currency0` in `_swapExactOutputSingle`

    breaking property:
    * the full debt of the wrong currency is returned, breaks the rule "all debt must be paid when pay full debt option is used"

V4Router_3

    code change:
    * make `_swap` always return 0

    breaking property:
    * `_swap` always returns 0, causing _swapExactInputSingle and other swap callers to revert in most acceptable cases

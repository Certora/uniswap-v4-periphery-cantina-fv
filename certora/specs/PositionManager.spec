import "./setup/SafeTransferLibCVL.spec";
import "./setup/Deltas.spec";
import "./setup/EIP712.spec";
import "./setup/PoolManager.spec";

using PositionManagerHarness as Harness;

methods {
    function getPoolAndPositionInfo(uint256 tokenId) external returns (PositionManagerHarness.PoolKey, PositionManagerHarness.PositionInfo) envfree;
    function Harness.poolManager() external returns (address) envfree;
    function Harness.msgSender() external returns (address) envfree;

    // summaries for unresolved calls
    unresolved external in _._ => DISPATCH [
        PositionManagerHarness._
    ] default NONDET;
    function _.permit(address,IAllowanceTransfer.PermitSingle,bytes) external => NONDET;
    function _.permit(address,IAllowanceTransfer.PermitBatch,bytes) external => NONDET;
    function _.isValidSignature(bytes32, bytes memory) internal => NONDET;
    function _.isValidSignature(bytes32, bytes) external => NONDET;
    function _._call(address, bytes memory) internal => NONDET;
    function _._call(address, bytes) external => NONDET;
    function _.notifyUnsubscribe(uint256, PositionManagerHarness.PositionInfo, bytes) external => NONDET;
    function _.notifyUnsubscribe(uint256, PositionManagerHarness.PositionInfo memory, bytes memory) internal => NONDET;
    function _.notifyUnsubscribe(uint256) external => NONDET;
    // likely unsound, but assumes no callback
    function _.onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes data
    ) external => NONDET; /* expects bytes4 */
}

use builtin rule sanity;

//  adding positive liquidity results in currency delta change for PositionManager
rule increaseLiquidityDecreasesBalances(env e) {
    uint256 tokenId; uint256 liquidity; uint128 amount0Max; uint128 amount1Max; bytes hookData;
    
    PositionManagerHarness.PoolKey poolKey; PositionManagerHarness.PositionInfo info;

    (poolKey, info) = getPoolAndPositionInfo(tokenId);
    require poolKey.hooks != currentContract;

    int256 delta0Before = getCurrencyDeltaExt(poolKey.currency0, currentContract);
    int256 delta1Before = getCurrencyDeltaExt(poolKey.currency1, currentContract);

    // deltas must be 0 at the start of any tx
    require delta0Before == 0;
    require delta1Before == 0;

    increaseLiquidity(e, tokenId, liquidity, amount0Max, amount1Max, hookData);

    int256 delta0After = getCurrencyDeltaExt(poolKey.currency0, currentContract);
    int256 delta1After = getCurrencyDeltaExt(poolKey.currency1, currentContract);

    assert liquidity != 0 => delta0After != 0 || delta1After != 0;
}


rule positionManagerSanctioned(address token, method f, env e, calldataarg args) filtered {
    f -> f.selector != sig:settlePair(Conversions.Currency,Conversions.Currency).selector
    && f.selector != sig:settle(Conversions.Currency,uint256,bool).selector
    && f.selector != sig:takePair(Conversions.Currency,Conversions.Currency,address).selector
    && f.selector != sig:take(Conversions.Currency,address,uint256).selector
    && f.selector != sig:close(Conversions.Currency).selector
    && f.selector != sig:sweep(Conversions.Currency,address).selector
    && f.contract == currentContract
} {
    require e.msg.sender == msgSender(e);
    require e.msg.sender != currentContract;

    uint256 balanceBefore = balanceOfCVL(token, currentContract);
    
    f(e,args);

    uint256 balanceAfter = balanceOfCVL(token, currentContract);

    assert balanceAfter == balanceBefore;
}


rule lockerDoesntChange(method f, env e, calldataarg args) {
    address locker = msgSender(e); // calls _getLocker

    f(e,args);

    address newLocker = msgSender(e);

    assert newLocker == locker;
}
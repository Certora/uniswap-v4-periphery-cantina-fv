// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import { PositionManager, IPoolManager, IAllowanceTransfer } from "src/PositionManager.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PositionConfig} from "src/libraries/PositionConfig.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import { SafeTransferLib } from "solmate/src/utils/SafeTransferLib.sol";


// This contract is added as a more efficient way to access internal actions. Note that _handleAction no longer performs any action. Keep in mind that in the actual contract, there are further requirements about the order of calls. For example, all actions must end in a take or a settle, so that deltas are zeroed out. 
contract PositionManagerHarness is PositionManager {
    constructor(IPoolManager _poolManager, IAllowanceTransfer _permit2, uint256 _unsubscribeGasLimit) 
    PositionManager(_poolManager, _permit2, _unsubscribeGasLimit) {}

    // override handlAction as its complex and just calls other functions in the contract. Can remove if wanted to prove specifics about where its called.
    function _handleAction(uint256 action, bytes calldata params) internal override {}

    // override multicall as its complex and just calls other functions in the scene, recommended to prove that a multicall is equivalent to executing two 
    function multicall(bytes[] calldata data) external payable override returns (bytes[] memory results) {}

    function settlePair(Currency currency0, Currency currency1) external {
        /// uint256 action = Actions.SETTLE_PAIR;
        _settlePair(currency0, currency1);
    }

    function takePair(Currency currency0, Currency currency1, address to) external {
        /// uint256 action = Actions.TAKE_PAIR;
        _takePair(currency0, currency1, to);
    }

    function settle(Currency currency, uint256 amount, bool payerIsUser) external {
        /// uint256 action = Actions.SETTLE;
        _settle(currency, _mapPayer(payerIsUser), _mapSettleAmount(amount, currency));
    }

    function take(Currency currency, address recipient, uint256 amount) external {
        /// uint256 action = Actions.TAKE;
         _take(currency, _mapRecipient(recipient), _mapTakeAmount(amount, currency));
    }

    function close(Currency currency) external {
        /// uint256 action = Actions.CLOSE_CURRENCY;
        _close(currency);
    }

    function clearOrTake(Currency currency, uint256 amountMax) external {
        /// uint256 action = Actions.CLEAR_OR_TAKE;
        _clearOrTake(currency, amountMax);
    }

    function sweep(Currency currency, address to) external {
        /// uint256 action = Actions.SWEEP;
        _sweep(currency, _mapRecipient(to));
    }

    function increaseLiquidity(
        uint256 tokenId,
        uint256 liquidity,
        uint128 amount0Max,
        uint128 amount1Max,
        bytes calldata hookData
    ) external {
        // uint256 action = Actions.INCREASE_LIQUIDITY;
        _increase(tokenId, liquidity, amount0Max, amount1Max, hookData);               
    }

    function decreaseLiquidity(
        uint256 tokenId,
        uint256 liquidity,
        uint128 amount0Min,
        uint128 amount1Min,
        bytes calldata hookData
    ) external {
        // uint256 action = Actions.DECREASE_LIQUIDITY;
        _decrease(tokenId, liquidity, amount0Min, amount1Min, hookData);             
    }

    function mintPosition(
        PoolKey calldata poolKey,
        int24 tickLower,
        int24 tickUpper,
        uint256 liquidity,
        uint128 amount0Max,
        uint128 amount1Max,
        address owner,
        bytes calldata hookData
    )  external {
        // uint256 action = Actions.MINT_POSITION;
        _mint(poolKey, tickLower, tickUpper, liquidity, amount0Max, amount1Max, _mapRecipient(owner), hookData);            
    }

    function burnPosition(
            uint256 tokenId,
            uint128 amount0Min,
            uint128 amount1Min,
            bytes calldata hookData
    ) external {
        // uint256 action = Actions.BURN_POSITION;
        // Will automatically decrease liquidity to 0 if the position is not already empty.
        _burn(tokenId, amount0Min, amount1Min, hookData);
    }
}
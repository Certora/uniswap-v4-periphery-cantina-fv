// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { PoolId } from "@uniswap/v4-core/src/types/PoolId.sol";
import { StateLibrary } from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
import { Position } from "@uniswap/v4-core/src/libraries/Position.sol";
import { TransientStateLibrary } from "@uniswap/v4-core/src/libraries/TransientStateLibrary.sol";
import { Slot0Library, Slot0 } from "@uniswap/v4-core/src/types/Slot0.sol";
import { IPoolManager } from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import { Currency } from "@uniswap/v4-core/src/types/Currency.sol";

contract PoolGetters {
    using StateLibrary for IPoolManager;
    using TransientStateLibrary for IPoolManager;
    
    IPoolManager private immutable manager;

    constructor(address _manager) {
        manager = IPoolManager(_manager);
    }

    function _getSlot0(PoolId poolId) internal view returns (bytes32) {
        bytes32 stateSlot = StateLibrary._getPoolStateSlot(poolId);
        return manager.extsload(stateSlot);
    }

    function getSqrtPriceX96(PoolId poolId) external view returns (uint160) {
        Slot0 packed = Slot0.wrap(_getSlot0(poolId));
        return Slot0Library.sqrtPriceX96(packed);
    }

    function getTick(PoolId poolId) external view returns (int24 _tick) {
        Slot0 packed = Slot0.wrap(_getSlot0(poolId));
        return Slot0Library.tick(packed);
    }

    function getProtocolFee(PoolId poolId) external view returns (uint24 _protocolFee) {
        Slot0 packed = Slot0.wrap(_getSlot0(poolId));
        return Slot0Library.protocolFee(packed);
    }

    function getLpFee(PoolId poolId) external view returns (uint24 _lpFee) {
        Slot0 packed = Slot0.wrap(_getSlot0(poolId));
        return Slot0Library.lpFee(packed);
    }

    function isUnlocked() external view returns (bool) {
        return manager.isUnlocked();
    }

    function getNonzeroDeltaCount() external view returns (uint256) {
        return manager.getNonzeroDeltaCount();
    }

    function getSyncedCurrency() external view returns (Currency) {
        return manager.getSyncedCurrency();
    }

    function getSyncedReserves() external view returns (uint256) {
        return manager.getSyncedReserves();
    }
}
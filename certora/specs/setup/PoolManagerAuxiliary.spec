import "./CVLMath.spec";

methods {
    function SqrtPriceMath.getNextSqrtPriceFromInput(
        uint160 sqrtPX96, uint128 liquidity, uint256 amountIn, bool zeroForOne
    ) internal returns (uint160) => NONDET;

    function SqrtPriceMath.getNextSqrtPriceFromOutput(
        uint160 sqrtPX96, uint128 liquidity, uint256 amountOut, bool zeroForOne
    ) internal returns (uint160) => NONDET;

    function SqrtPriceMath.getAmount0Delta(
        uint160 sqrtRatioAX96, uint160 sqrtRatioBX96, uint128 liquidity, bool roundUp
    ) internal returns (uint256) => NONDET;
    
    function SqrtPriceMath.getAmount1Delta(
        uint160 sqrtRatioAX96, uint160 sqrtRatioBX96, uint128 liquidity, bool roundUp
    ) internal returns (uint256) => NONDET;

    function TickMath.getSqrtPriceAtTick(int24 tick) internal returns (uint160) => NONDET;
    function TickMath.getTickAtSqrtPrice(uint160 sqrtPriceX96) internal returns (int24) => NONDET;

    function FullMath.mulDiv(uint256 a, uint256 b, uint256 denominator) internal returns (uint256) => mulDivDownCVL(a,b,denominator);
    function FullMath.mulDivRoundingUp(uint256 a, uint256 b, uint256 denominator) internal returns (uint256) => mulDivUpCVL(a,b,denominator);
    function UnsafeMath.divRoundingUp(uint256 x, uint256 y) internal returns (uint256) => divUpCVL(x,y);

    function PoolManager.extsload(bytes32 slot) external returns (bytes32) => NONDET DELETE;
    function PoolManager.extsload(bytes32[] slots) external returns (bytes32[] memory) => ArbBytes32(slots) DELETE;
    function PoolManager.extsload(bytes32 startSlot, uint256 nSlots) external returns (bytes32[] memory) => ArbNBytes32(startSlot, nSlots) DELETE;
    function PoolManager.exttload(bytes32[] slots) external returns (bytes32[] memory) => ArbBytes32(slots) DELETE;
    function ParseBytes.parseSelector(bytes memory) internal returns (bytes4) => NONDET;

    function TickBitmap.nextInitializedTickWithinOneWord(
        mapping(int16 => uint256) storage,
        int24 tick,
        int24 tickSpacing,
        bool lte
    ) internal returns (int24,bool) => NONDET;

    function Position.calculatePositionKey(address owner, int24 tickLower, int24 tickUpper, bytes32 salt) internal returns(bytes32) => 
        getPositionKey(owner, tickLower, tickUpper, salt);

    function PoolGetters._getSlot0(PoolManager.PoolId poolId) internal returns (bytes32) => getSlot0Direct(poolId);
}

function ArbNBytes32(bytes32 startSlot, uint256 nSlots) returns bytes32[] {
    bytes32[] data;
    require data.length == nSlots;
    return data;
}

function ArbBytes32(bytes32[] slots) returns bytes32[] {
    bytes32[] data;
    require data.length == slots.length;
    return data;
}

function getActiveLiquidity(Conversions.PoolId poolId) returns uint128 {
    return PM._pools[poolId].liquidity;
}

function getPositionLiquidityDirect(Conversions.PoolId poolId, bytes32 positionId) returns uint128 {
    return PM._pools[poolId].positions[positionId].liquidity;
}

function getSlot0Direct(Conversions.PoolId poolId) returns bytes32 {
    return PM._pools[poolId].slot0;
}
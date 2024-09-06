definition NATIVE() returns address = 0;

function validTicks(int24 tickLower, int24 tickUpper) returns bool {
    return (tickLower < tickUpper);
}

function isActivePosition(int24 tick0, int24 tickLower, int24 tickUpper) returns bool {
    return tick0 >= tickLower && tick0 < tickUpper;
}

function amountsToBalanceDelta(int128 _amount0, int128 _amount1) returns Conversions.BalanceDelta 
{
    Conversions.BalanceDelta delta;
    require Conv.amount0(delta) == _amount0;
    require Conv.amount1(delta) == _amount1;
    return delta;
}
import "../ERC20/erc20cvl.spec";

using FallbackCaller as FallbackCaller;

methods {
    function SafeTransferLib.safeTransferETH(address recipient, uint256 amount) internal with (env e) => dispatchTransferEth(e, calledContract, recipient, amount);
    function SafeTransferLib.safeTransfer(address token, address recipient, uint256 amount) internal with (env e) => dispatchTransfer(e, calledContract, token, recipient, amount);
    function SafeTransferLib.safeTransferFrom(address token, address sender, address recipient, uint256 amount) internal with (env e) => dispatchTransferFrom(e, calledContract, token, sender, recipient, amount);
    function SafeTransferLib.safeApprove(address token, address to, uint256 amount) internal with (env e) => dispatchApprove(e, calledContract, token, to, amount);
}

function dispatchTransferEth(env e, address caller, address recipient, uint256 amount)  {
    env ed; /// Dispatch environment
    require ed.msg.sender == caller;
    require ed.block.timestamp == e.block.timestamp; 

    FallbackCaller.callFallback(ed, recipient, amount);
}

function dispatchTransfer(env e, address caller, address token, address recipient, uint256 amount) {
    bool success = transferCVL(token,caller,recipient,amount);
    require success;
}

function dispatchTransferFrom(env e, address caller, address token, address sender, address recipient, uint256 amount) {
    bool success = transferFromCVL(token, caller, sender, recipient, amount);
    require success;
}

function dispatchApprove(env e, address caller, address token, address to, uint256 amount) {
    bool success = approveCVL(token, caller, to, amount);
    require success;
}

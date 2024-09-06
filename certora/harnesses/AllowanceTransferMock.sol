// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {SafeTransferLib} from "solmate/src/utils/SafeTransferLib.sol";
import { ERC20 } from "solmate/src/tokens/ERC20.sol";

interface IAllowanceTransferMock {
    function permit(address owner, IAllowanceTransfer.PermitSingle memory permitSingle, bytes calldata signature) external;
    function permit(address owner, IAllowanceTransfer.PermitBatch memory permitBatch, bytes calldata signature) external;
    function transferFrom(address from, address to, uint160 amount, address token) external;
}

contract AllowanceTransferMock is IAllowanceTransferMock {
    using SafeTransferLib for ERC20;

    /// The owner of the tokens being approved
    address single_owner;
    // ERC20 token address
    address single_token;
    // the maximum amount allowed to spend
    uint160 single_amount;
    // timestamp at which a spender's token allowances become invalid
    uint48 single_expiration;
    // an incrementing value indexed per owner,token,and spender for each signature
    uint48 single_nonce;
    // address permissioned on the allowed tokens
    address single_spender;
    // deadline on the permit signature
    uint256 single_sigDeadline;
    /// The hash of owner's signature over the permit data
    bytes32 single_signature_hash;

    function permit(address owner, IAllowanceTransfer.PermitSingle memory permitSingle, bytes calldata signature) external {
        single_owner = owner;
        single_token = permitSingle.details.token;
        single_amount = permitSingle.details.amount;
        single_expiration = permitSingle.details.expiration;
        single_nonce = permitSingle.details.nonce;
        single_spender = permitSingle.spender;
        single_sigDeadline = permitSingle.sigDeadline;
        single_signature_hash = keccak256(abi.encode(signature));
    }

    /// The owner of the tokens being approved
    address batch_owner;
    // ERC20 token address
    address[] batch_token;
    // the maximum amount allowed to spend
    uint160[] batch_amount;
    // timestamp at which a spender's token allowances become invalid
    uint48[] batch_expiration;
    // an incrementing value indexed per owner,token,and spender for each signature
    uint48[] batch_nonce;
    // address permissioned on the allowed tokens
    address batch_spender;
    // deadline on the permit signature
    uint256 batch_sigDeadline;
    /// The hash of owner's signature over the permit data
    bytes32 batch_signature_hash;

    function permit(address owner, IAllowanceTransfer.PermitBatch memory permitBatch, bytes calldata signature) external {
        batch_owner = owner;
        uint256 length = permitBatch.details.length;
        for (uint256 i = 0; i < length; ++i) {
            batch_token[i] = permitBatch.details[i].token;
            batch_amount[i] = permitBatch.details[i].amount;
            batch_expiration[i] = permitBatch.details[i].expiration;
            batch_nonce[i] = permitBatch.details[i].nonce;
        }
        batch_spender = permitBatch.spender;
        batch_sigDeadline = permitBatch.sigDeadline;
        batch_signature_hash = keccak256(abi.encode(signature));
    }

    function transferFrom(address from, address to, uint160 amount, address token) external {
        _transfer(from, to, amount, token);
    }

    function _transfer(address from, address to, uint160 amount, address token) private {
        /*IAllowanceTransfer.PackedAllowance storage allowed = allowance[from][token][msg.sender];

        if (block.timestamp > allowed.expiration) revert (); //AllowanceExpired(allowed.expiration);

        uint256 maxAmount = allowed.amount;
        if (maxAmount != type(uint160).max) {
            if (amount > maxAmount) {
                revert ();//InsufficientAllowance(maxAmount);
            } else {
                unchecked {
                    allowed.amount = uint160(maxAmount) - amount;
                }
            }
        }*/

        // Transfer the tokens from the from address to the recipient.
        ERC20(token).safeTransferFrom(from, to, amount);
    }
}
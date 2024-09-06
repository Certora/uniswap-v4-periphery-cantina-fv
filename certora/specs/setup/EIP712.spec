using AllowanceTransferMock as AllowanceTransfer;

methods {
    /// EIP712
    function PositionManagerHarness.DOMAIN_SEPARATOR() external returns (bytes32) => CONSTANT DELETE;
    function _._hashTypedData(bytes32 dataHash) internal => hashTypedDataEIP712(calledContract,dataHash) expect bytes32;
}

ghost hashTypedDataEIP712(address,bytes32) returns bytes32 {
    axiom forall address self. forall bytes32 hash1. forall bytes32 hash2.
        hash1 != hash2 => hashTypedDataEIP712(self, hash1) != hashTypedDataEIP712(self, hash2);
}
import "./ERC20/erc20cvl.spec";

// summaries for unresolved calls
methods {
    function _.unlock(bytes) external => NONDET;
    unresolved external in Quoter.unlockCallback(bytes) => DISPATCH[
        Quoter._
    ] default NONDET;
    
}

use builtin rule sanity filtered { f -> f.contract == currentContract && !knownFailingSanity(f) }

// workarounds for crashes
definition knownFailingSanity(method f) returns bool = 
    f.selector == sig:_quoteExactInputSingle(IQuoter.QuoteExactSingleParams).selector ||
    f.selector == sig:_quoteExactOutputSingle(IQuoter.QuoteExactSingleParams).selector ||
    f.selector == sig:_quoteExactInput(IQuoter.QuoteExactParams).selector ||
    f.selector == sig:_quoteExactOutput(IQuoter.QuoteExactParams).selector ||
    f.selector == sig:unlockCallback(bytes).selector;
# Security invariants and disclosure

The following are load-bearing:

- the Finality Sink reconstructs the actual effect rather than accepting app-supplied hashes;
- validator and requester keys have distinct roles;
- the capability is unusable without proof of possession of the registered requester key;
- LAVR and capability signatures, digests, epochs, sink, boundary, nonce, time, and act commitment are all verified;
- no alternative message-send path bypasses finality verification;
- revocation and governance epochs are checked again at finality;
- effect commit and authority consumption are one crash-consistent transaction;
- remote completion is not inferred merely from local authority consumption.

The portable SQLite adapter does not provide hardware rollback resistance. Real deployments must replace it or protect it appropriately.


# Secure AI-Assistant Interoperability: Execution-Finality Implementation

This repository implements a bounded, runnable reference profile derived from `draft-das-execution-finality-ai-interoperability-02`.

It models a third-party or first-party assistant requesting that the operating system send one exact resource to one exact recipient. The assistant can propose the operation but cannot directly effectuate it. A protected validator creates a signed validation receipt (LAVR) and a signed, app-key-bound capability. The message Finality Sink reconstructs the actual release state and commits only if every binding still matches.

## Implemented security properties

- **Candidate Device Act:** deterministic CBOR commitment over requester, action, resource digest, recipient, destination app, sink, boundary, user-intent evidence, session, epochs, nonce, and validity.
- **Protected validation:** one fail-closed path checks requester registration, permitted action, destination app, fresh user confirmation, current policy/security/revocation epochs, revocation, and time.
- **Pre-effect validation receipt:** the COSE_Sign1 LAVR records the act commitment, passed predicate names, nonce, policy state, sink, and boundary before authority exists.
- **Fractional capability:** a separate COSE_Sign1 object binds one act, LAVR digest, requester-key thumbprint, sink, boundary, epochs, nonce, expiry, and one permitted effect.
- **Non-bearer presentation:** the requesting app signs a fresh presentation over the capability digest and actual-effect commitment. Copying the capability without the app key is insufficient.
- **Finality verification:** the sink validates both signatures, LAVR/capability linkage, proof of possession, actual reconstructed consequence, sink/boundary, time, current governance state, revocation, and consumption state.
- **Crash-consistent local effect:** nonce consumption, state transitions, and the simulated message commit occur in one SQLite `BEGIN IMMEDIATE` transaction.
- **Parity:** first-party and third-party assistants go through the same validator and sink code paths.

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
python scripts/benchmark.py | tee benchmark-results.txt
```

The test suite contains **9 executable tests** demonstrating:

1. the exact authorized message commits once and replay cannot create a second effect;
2. recipient substitution fails;
3. resource substitution fails;
4. a stolen capability fails without the assistant key;
5. presentation to another Finality Sink fails;
6. revocation after issuance prevents effectuation;
7. changed policy/security/revocation epochs invalidate old authority;
8. absence of verified user intent prevents issuance; and
9. first-party and third-party requesters use equivalent predicates.

## Trust boundaries

`ProtectedValidator` represents PED/CIED functionality. `FinalitySink` represents an OS-controlled message-send boundary. `ProtectedState` represents rollback-protected state. In this portable implementation these are process and SQLite abstractions so the protocol can be executed and tested on ordinary computers.

A real Android, iOS, desktop, or embedded integration must replace those adapters with platform primitives:

- hardware-backed app keys and key attestation;
- authenticated application identity from the package/code-signing subsystem;
- a trusted UI surface for exact-act confirmation;
- protected monotonic epoch and replay state;
- OS message/file/network controllers with no bypass route;
- rollback-resistant storage or a trusted remote state service;
- platform policy distribution and revocation;
- a measured and attested Finality Boundary Manifest;
- receiver-side idempotency for exactly-once external semantics.

This code cannot create those OS privileges from user space. Claiming otherwise would be misleading.

## Production hardening checklist

- Move validator keys into Secure Enclave, StrongBox, TPM, HSM, or KMS-backed signing.
- Bind requester public keys to verified package identity and code-signing state.
- Replace the Boolean user-intent adapter with a trusted-path confirmation receipt bound to the Candidate Act commitment.
- Place every governed send/export/dispatch route downstream of the corresponding Finality Sink.
- Protect the SQLite database against rollback, or replace it with transactional protected storage.
- Separate authority state from remote completion state; use stable `act_id` as the receiver idempotency key.
- Add authenticated IPC, request quotas, bounded queues, deadlines, metrics, audit export, key rotation, disaster recovery, and privacy retention rules.
- Fuzz deterministic CBOR/COSE parsers and obtain independent cryptographic and OS-security review.
- Validate accessibility workflows without weakening the exact-act or anti-replay predicates.
- Publish conformance vectors for equivalent first-party and third-party operations.

## Rights and licensing

The repository is source-available under the terms in `LICENSE`. The included license permits inspection, security review, interoperability evaluation, and non-production testing, while reserving commercial implementation, distribution, derivative-work, and patent licensing rights unless separately granted in writing. It is therefore **not presented as an OSI-approved open-source license**.

## Honest scope

This repository is working protocol and enforcement code for a narrow message-send profile. It is not an Apple or Android system component, has not been reviewed by either platform vendor, and is not proof of DMA compliance. It demonstrates feasibility of the cryptographic and state-machine design; OS-vendor cooperation is required to make the Finality Sink non-bypassable on a commercial device.


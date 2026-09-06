Secure AI-Assistant Interoperability: Execution-Finality Implementation

This repository provides a bounded, runnable reference implementation derived from:

draft-das-execution-finality-ai-interoperability
https://datatracker.ietf.org/doc/draft-das-execution-finality-ai-interoperability/

The implementation demonstrates a technical model for allowing a first-party or third-party AI assistant to request a tightly scoped device action without granting the assistant unrestricted operating-system authority.

The core architectural rule is:

The assistant may propose the action, but the assistant does not itself possess authority to make the action externally effective.

Instead, the assistant creates a Candidate Device Act. A protected validation component evaluates that exact act, produces pre-effect validation evidence, and derives a narrowly scoped authority bound to the validated operation. The operating-system-controlled Finality Sink then reconstructs the real effect that is about to occur and permits completion only if the validated act, current system state, destination, recipient, requester, user intent, security epochs, and one-time authority all still match.

The reference profile uses a simple example: an assistant requests that the operating system send one exact resource to one exact recipient through one exact destination application.

The design is intended to demonstrate a possible technical middle ground between two undesirable extremes:

refusing meaningful interoperability because third-party AI assistants cannot safely be given unrestricted OS authority; and
granting third-party assistants broad privileged access that creates unacceptable security, privacy, impersonation, or data-exfiltration risks.

The architecture attempts to make interoperability capability-specific, act-specific, user-intent-bound, revocable, non-bearer, and independently re-verified at the point of external effectuation.

Why this matters for Apple/Siri, Android, and the EU Digital Markets Act

A central technical difficulty in AI-assistant interoperability is that operating systems perform sensitive actions on behalf of users: sending messages, sharing files, opening applications, invoking device functions, accessing protected data, communicating with contacts, or causing other externally visible effects.

A platform vendor can reasonably argue that giving a third-party AI assistant the same unrestricted authority as a deeply integrated first-party assistant could create serious security and privacy risks.

At the same time, interoperability requirements can create pressure for third-party assistants to interact meaningfully with platform functionality rather than being permanently restricted to a limited application sandbox.

The execution-finality model addresses this architectural conflict by separating:

ability to request an operation

from:

authority to complete that operation.

A third-party assistant therefore does not need to receive a master OS credential, unrestricted IPC capability, broad message-send privilege, permanent user impersonation authority, or generic bearer token.

Instead, the assistant can request:

“Send this exact file to this exact recipient through this exact application, based on this exact user-confirmed instruction.”

The operating system can then independently validate that request and issue authority that is usable only for that exact act.

The resulting sequence is:

AI assistant proposes operation
        ↓
Candidate Device Act
        ↓
Protected Validator / PED / CIED
        ↓
User-intent + policy + requester + destination validation
        ↓
Pre-effect validation receipt (LAVR)
        ↓
Scoped app-key-bound fractional capability
        ↓
Proof-of-possession presentation
        ↓
OS-controlled Finality Sink
        ↓
Reconstruction of the actual consequence
        ↓
Atomic one-time consumption
        ↓
External effect

This means the operating system remains the authority boundary.

The assistant remains a proposer.

That distinction is particularly relevant to the Apple/Siri and third-party-assistant interoperability problem.

A third-party assistant such as another AI provider could potentially request approved device actions while the platform continues to retain control of:

application identity;
user confirmation;
protected resources;
permitted action classes;
revocation;
destination identity;
device policy;
secure storage;
message dispatch;
network release;
key custody;
replay state;
and the final externally effective boundary.

The architecture therefore does not require the platform to turn a third-party assistant into a privileged substitute for the operating system.

Instead, it creates a possible interoperability model in which:

permission to ask is broad, but authority to effectuate remains fractional and exact.

This can be relevant to EU Digital Markets Act interoperability discussions because it provides a technical approach for exposing useful assistant functionality without assuming that interoperability necessarily means unrestricted delegation of platform authority.

The repository does not claim that this implementation itself satisfies the DMA, resolves any particular regulatory proceeding, or represents an Apple, Google, European Commission, or platform-vendor implementation. It demonstrates a technical architecture that could be evaluated as one possible means of reconciling interoperability with platform security.

Implemented Security Properties
1. Candidate Device Act

The assistant begins by constructing a deterministic Candidate Device Act.

The act contains the exact state necessary to identify the proposed consequence, including:

requester identity;
requested action;
resource digest;
recipient;
destination application;
Finality Sink;
Finality Boundary;
user-intent evidence;
session;
policy epoch;
security epoch;
revocation epoch;
nonce;
validity period.

The Candidate Device Act is encoded using deterministic CBOR so that every component evaluates the same committed representation.

Changing any load-bearing field changes the act commitment.

The proposed operation therefore cannot be silently mutated after validation without invalidating the later cryptographic checks.

2. Protected Validation

ProtectedValidator represents the protected enforcement function described in the architecture as PED/CIED functionality.

The validator follows a fail-closed path.

It checks conditions including:

whether the requester is registered;
whether the requested action is permitted;
whether the destination application is allowed;
whether fresh user confirmation is present;
whether the policy epoch remains current;
whether the security epoch remains current;
whether the revocation epoch remains current;
whether the requester has been revoked;
whether the request is still temporally valid.

There is no default-allow path.

Failure of a required predicate prevents authority from being created.

3. Pre-Effect Validation Receipt

Successful validation produces a signed LAVR before final authority exists.

The LAVR is represented as a COSE_Sign1 object and records information including:

Candidate Act commitment;
successful predicate names;
nonce;
policy state;
sink identity;
Finality Boundary;
relevant epochs.

This preserves the ordering:

Candidate Act
    ↓
Validation
    ↓
Validation Evidence
    ↓
Authority
    ↓
Effect

rather than:

Effect
    ↓
Audit log

The distinction is important.

The validation receipt is part of the pre-effect authorization chain rather than merely evidence generated after an action has already happened.

4. Fractional Capability

After successful validation, the protected validator creates a separate signed capability.

The capability is deliberately narrow.

It is cryptographically bound to:

one Candidate Device Act;
the LAVR digest;
the requester-key thumbprint;
the intended Finality Sink;
the Finality Boundary;
current epochs;
nonce;
expiry;
one permitted effect.

It is therefore a fractional capability, not a general-purpose OS credential.

The assistant does not receive permission such as:

“Send messages.”

It receives authority closer to:

“This validated requester may attempt this exact previously validated effect under these exact conditions before this authority expires.”

5. Non-Bearer Presentation

Possession of the capability alone is insufficient.

The requesting application must create a fresh proof-of-possession presentation using the application-bound private key.

The presentation is bound to:

the capability digest;
the reconstructed actual-effect commitment;
the requesting application key.

This prevents a copied capability from functioning as a conventional bearer token.

An attacker who steals the capability but does not possess the corresponding protected application key cannot simply replay it from another application.

This property is particularly important for cross-assistant interoperability because the OS does not need to trust a capability merely because a process presents its bytes.

Why Non-Bearer Authority Matters for AI Assistants

AI agents frequently interact through tool calls, APIs, plugins, IPC boundaries, remote services, and application brokers.

A conventional bearer credential can create an uncomfortable security property:

Whoever possesses the credential may be able to exercise the authority.

That is particularly risky where AI-generated tool arguments are dynamic.

The execution-finality model instead attempts to bind authority simultaneously to:

WHO
+
WHAT
+
WHICH RESOURCE
+
WHICH RECIPIENT
+
WHICH DESTINATION
+
WHICH SINK
+
WHICH POLICY STATE
+
WHICH USER INTENT
+
WHICH TIME WINDOW
+
WHICH ONE-TIME ACT

Authority therefore becomes an attribute of the validated act rather than a reusable privilege possessed by the AI model.

6. Finality Sink Verification

The Finality Sink is the most important enforcement boundary in the profile.

The sink does not simply trust the assistant's request or even trust the previously generated capability.

It reconstructs the actual release state at the point where the consequence is about to occur.

It verifies:

LAVR signature;
capability signature;
LAVR/capability linkage;
proof of possession;
Candidate Act commitment;
actual resource;
actual recipient;
actual destination;
actual requester;
sink identity;
Finality Boundary;
validity time;
policy epoch;
security epoch;
revocation epoch;
revocation status;
nonce;
authority consumption state.

Only after all required state matches does the Finality Sink permit the external effect.

This prevents a previously valid authorization from automatically remaining valid when the real consequence has changed.

Example: Siri / Third-Party Assistant Message Interoperability

Consider a user saying to a third-party assistant:

Send report.pdf to Alice using the approved messaging application.

The third-party assistant may determine the desired operation and construct a Candidate Device Act.

But it does not receive a generic operating-system message privilege.

Instead:

Step 1 — Candidate Act

The request identifies:

assistant = ThirdPartyAssistant
action = SEND_RESOURCE
resource = SHA256(report.pdf)
recipient = Alice
destination = ApprovedMessagingApp
sink = OS_Message_Send_Sink
Step 2 — OS validation

The protected validator checks:

that the assistant is registered;
that message sending is an allowed interoperable operation;
that this destination app is approved;
that Alice is the actual selected recipient;
that the user has confirmed this exact action;
that current policy and security state permits it.
Step 3 — LAVR

A pre-effect validation receipt is created.

Step 4 — Fractional authority

A one-act capability is issued.

The capability cannot be reused to send another file to Bob.

It cannot be reused to send report.pdf through another app.

It cannot be used after expiry.

It cannot be used after revocation.

It cannot be used by another application that does not hold the corresponding protected key.

Step 5 — Finality

Immediately before message dispatch, the operating system reconstructs:

actual resource
actual recipient
actual destination
actual requester
actual policy state

If the actual recipient is Bob instead of Alice:

DENY

If the file changed:

DENY

If the destination changed:

DENY

If the capability was stolen:

DENY

If the requester has since been revoked:

DENY

Only the exact previously validated operation reaches:

COMMIT

This is the central interoperability property demonstrated by the repository.

First-Party / Third-Party Parity

The reference profile deliberately sends first-party and third-party assistant requests through equivalent validation predicates and Finality Sink logic.

This is an important architectural property.

A platform could define legitimate security requirements such as:

user intent;
app identity;
protected application key;
approved action class;
destination binding;
revocation;
freshness;
anti-replay;
exact-act reconstruction.

Those requirements can be applied to both first-party and third-party assistants.

The security rule therefore does not need to become:

IF first_party:
    allow
ELSE:
    deny

Instead:

IF required_security_predicates_satisfied:
    issue_fractional_authority
ELSE:
    deny

This provides a technically testable notion of interoperability parity while allowing the operating system to preserve its security boundary.

Crash-Consistent Local Effect

The implementation uses a SQLite BEGIN IMMEDIATE transaction to coordinate:

nonce consumption;
authority state;
state transition;
simulated message commit.

This makes replay and concurrency behavior directly executable and inspectable.

The implementation is intentionally narrow and conservative.

SQLite is used because it makes the state machine easy to audit and reproduce on an ordinary computer.

It is not presented as the required storage mechanism for an Android, iOS, accelerator, secure enclave, or production OS implementation.

Executable Test Suite

The repository includes 9 executable tests demonstrating:

the exact authorized message commits once and replay cannot create a second effect;
recipient substitution fails;
resource substitution fails;
a stolen capability fails without the assistant key;
presentation to another Finality Sink fails;
revocation after issuance prevents effectuation;
changed policy/security/revocation epochs invalidate old authority;
absence of verified user intent prevents issuance; and
first-party and third-party requesters use equivalent predicates.

These tests demonstrate specific state-machine and cryptographic properties of the reference implementation.

They are not a claim of production security certification.

Run
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
python scripts/benchmark.py | tee benchmark-results.txt

On Windows PowerShell, virtual-environment activation may instead be:

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python -m unittest discover -s tests -v
python scripts\benchmark.py
Trust Boundaries

ProtectedValidator represents PED/CIED functionality.

FinalitySink represents an OS-controlled message-send Finality Sink.

ProtectedState represents rollback-protected security and authority state.

In this portable implementation these are process and SQLite abstractions so that the protocol can be executed, reviewed, attacked, and tested on an ordinary computer.

A production mobile-platform implementation would require those logical components to be mapped to actual trusted platform primitives.

What an Android or iOS Integration Would Require

A commercial implementation should replace the reference adapters with platform mechanisms such as:

hardware-backed application keys;
key attestation;
authenticated package identity;
code-signing identity;
protected application registration;
trusted UI for exact-act confirmation;
protected monotonic policy state;
protected security epochs;
protected revocation epochs;
rollback-resistant replay state;
OS message controllers;
OS file/export controllers;
protected network-release boundaries;
protected IPC;
DMA/IOMMU controls where relevant;
platform policy distribution;
secure revocation;
measured Finality Boundary manifests;
platform attestation;
receiver-side idempotency.

The Finality Sink must sit on the path through which the governed consequence becomes externally effective.

If an equivalent bypass path remains available, the Finality Sink cannot provide strong enforcement for that effect class.

Why the Finality Sink Cannot Simply Be Implemented as an Ordinary App

A user-space application cannot reliably guarantee that every operating-system communication, file transfer, privileged action, IPC path, hardware interface, or platform service passes through its code.

For this reason, the reference implementation does not claim that Python code can independently impose a non-bypassable security boundary on iOS or Android.

A production implementation requires OS-vendor or platform-level integration.

That is not a weakness hidden by this repository; it is an explicit architectural requirement.

The purpose of the implementation is to demonstrate the protocol logic and state transitions that the trusted platform boundary would enforce.

Production Hardening Checklist

A production implementation should consider the following.

Move validator keys into Secure Enclave, StrongBox, TPM, HSM, protected firmware, or KMS-backed signing.
Bind requester public keys to verified application/package identities.
Bind keys to relevant code-signing state.
Replace Boolean user-intent input with a trusted-path confirmation receipt.
Bind user confirmation cryptographically to the Candidate Act commitment.
Place every governed send/export/dispatch route downstream of an appropriate Finality Sink.
Use rollback-resistant protected state.
Separate authority-consumption state from remote completion state.
Use stable act_id values for receiver-side idempotency.
Add authenticated IPC.
Add request quotas and bounded queues.
Define timeouts and deadline behavior.
Add metrics and privacy-controlled audit export.
Implement key rotation.
Define disaster recovery.
Define authority state recovery after crashes.
Define privacy-retention rules.
Fuzz deterministic CBOR and COSE parsing.
Obtain independent cryptographic review.
Obtain independent OS-security review.
Validate accessibility workflows without weakening exact-act binding.
Publish first-party/third-party conformance vectors.
What the Architecture Does Not Require

The execution-finality architecture does not inherently require giving a third-party AI assistant:

unrestricted root privileges;
permanent message-send authority;
unrestricted access to first-party application data;
a generic OS signing key;
broad filesystem access;
universal contact access;
unrestricted IPC;
reusable bearer credentials;
direct ownership of the Finality Sink.

The platform can retain all of those controls.

The assistant instead receives access to a protocol for proposing actions and, where validation succeeds, presenting bounded authority for one exact effect.

Interoperability Without Unrestricted Authority

This is the principal design objective.

The architecture attempts to demonstrate that the choice need not be:

NO INTEROPERABILITY

or:

FULL PRIVILEGED ACCESS

A third possibility is:

INTEROPERABILITY
+
EXACT-ACT VALIDATION
+
NON-BEARER AUTHORITY
+
OS FINALITY CONTROL

That model could support third-party AI assistants while preserving a technically meaningful platform security boundary.

For the Apple/Siri and EU DMA context, this is the key proposition:

A platform can expose interoperable functionality without transferring unrestricted platform authority to the interoperating AI assistant.

Performance and Latency

The architecture is also designed so that Finality enforcement does not inherently have to sit inside every internal model-computation step.

For example, internal operations such as:

token generation;
speculative decoding;
attention;
tensor movement;
internal model state;
expert routing;
embedding computation;

do not automatically need to become Candidate Device Acts.

The Candidate Act is created when a consequential platform operation is proposed.

This allows normal AI computation to remain separate from the stronger effectuation path.

Production implementations could also:

cache stable policy state;
batch validation;
maintain protected local epochs;
colocate validation with OS services;
use accelerator or secure-enclave primitives;
pre-provision narrowly bounded authority where safe;
perform local verification without remote network calls.

The protocol therefore does not inherently require a remote authorization round trip for every token generated by an AI assistant.

Security Principle

The implementation is based on a simple distinction:

Model output ≠ authority
Tool call ≠ authority
Application request ≠ authority
Possession of capability ≠ authority
Successful earlier validation ≠ permanent authority

External effect requires the complete validation and Finality chain.

In compact form:

Candidate Device Act
        ↓
Protected Validation
        ↓
LAVR
        ↓
Scoped Non-Bearer Fractional Capability
        ↓
Proof of Possession
        ↓
Finality Sink Reconstruction
        ↓
Current-State Verification
        ↓
Atomic Consumption
        ↓
External Effect
Full Technical Disclosure

This GitHub repository intentionally implements a bounded reference profile rather than attempting to reproduce every architectural embodiment in code.

Readers interested in the complete protocol architecture, interoperability model, terminology, security rationale, deployment considerations, and broader execution-finality design are respectfully encouraged to review the associated Internet-Draft:

Secure AI-Assistant Interoperability Using Execution-Finality — draft-das-execution-finality-ai-interoperability
https://datatracker.ietf.org/doc/draft-das-execution-finality-ai-interoperability/

The Internet-Draft should be treated as the fuller technical disclosure of the architecture, while this repository provides a runnable implementation intended to make selected protocol properties concrete and independently testable.

Rights and Licensing

The repository is source-available under the terms in LICENSE.

The included license permits inspection, security review, interoperability evaluation, and non-production testing while reserving commercial implementation, distribution, derivative-work, and patent licensing rights unless separately granted in writing.

It is therefore not presented as an OSI-approved open-source license.

Publication of source code should not be interpreted as granting rights beyond those expressly stated in the repository license or any separately applicable patent or standards disclosure.

Honest Scope

This repository contains working protocol and enforcement code for a deliberately narrow message-send interoperability profile.

It is:

a runnable technical reference;
a cryptographic/state-machine implementation;
an interoperability experiment;
a conformance starting point;
a platform-integration design reference.

It is not:

an Apple system component;
a Siri implementation;
an Android system component;
a Google implementation;
an EU-approved compliance mechanism;
proof of DMA compliance;
proof that platform integration can be performed without vendor cooperation;
a production-certified security implementation.

Neither Apple nor Google has reviewed or endorsed this repository.

The European Commission has not certified this implementation as a DMA solution.

The repository demonstrates the feasibility of the bounded-authority, exact-act, Finality-Sink protocol logic in executable form.

A commercial mobile implementation would require cooperation from, or implementation by, the platform vendor so that the Finality Sink becomes part of a genuinely non-bypassable operating-system boundary.

The broader proposition is therefore intentionally narrower and more defensible:

Secure AI-assistant interoperability does not necessarily require unrestricted delegation of operating-system authority. A platform can instead retain final authority while exposing narrowly bounded, cryptographically validated, one-act interoperability paths to first-party and third-party assistants.


# Secure AI-Assistant Interoperability: Execution-Finality Implementation

## This repository provides a bounded, runnable reference implementation derived from:

draft-das-execution-finality-ai-interoperability
https://datatracker.ietf.org/doc/draft-das-execution-finality-ai-interoperability/

### The implementation demonstrates a technical model for allowing a first-party or third-party AI assistant to request a tightly scoped device action without granting the assistant unrestricted operating-system authority.

The core architectural rule is:

The assistant may propose the action, but the assistant does not itself possess authority to make the action externally effective.

Instead, the assistant creates a Candidate Device Act. A protected validation component evaluates that exact act, produces pre-effect validation evidence, and derives a narrowly scoped authority bound to the validated operation. The operating-system-controlled Finality Sink then reconstructs the real effect that is about to occur and permits completion only if the validated act, current system state, destination, recipient, requester, user intent, security epochs, and one-time authority all still match.

The reference profile uses a simple example: an assistant requests that the operating system send one exact resource to one exact recipient through one exact destination application.

The design is intended to demonstrate a possible technical middle ground between two undesirable extremes:

refusing meaningful interoperability because third-party AI assistants cannot safely be given unrestricted OS authority; and
granting third-party assistants broad privileged access that creates unacceptable security, privacy, impersonation, or data-exfiltration risks.

The architecture attempts to make interoperability capability-specific, act-specific, user-intent-bound, revocable, non-bearer, and independently re-verified at the point of external effectuation.

## Why this matters for Apple/Siri, Android, and the EU Digital Markets Act

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

### That distinction is particularly relevant to the Apple/Siri and third-party-assistant interoperability problem.

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

## Why OAuth at the Final Execution Boundary Is Still Not Automatically Execution Finality

### Technical Note on Authorization, Final Effectuation, and Functional Equivalence

A recurring question in discussions of execution-finality architecture is:

**If OAuth is enforced at the final or irreversible execution boundary, and the authorization is sender-constrained or otherwise non-bearer, why is any additional execution-finality architecture required?**

The answer is that **placement at the final boundary and possession resistance are necessary properties in some deployments, but they are not by themselves sufficient to establish execution finality.**

The distinction is functional rather than terminological.

OAuth, Rich Authorization Requests, proof-of-possession mechanisms, sender-constrained tokens, transaction tokens, workload identity, or equivalent authorization mechanisms may all provide useful inputs to an execution-finality system.

However, a system reaches execution-finality semantics only when the component controlling the actual consequence verifies the complete relationship between:

- what was authorized;
- what is actually about to happen;
- the current protected system state;
- freshness and replay state;
- revocation or generation state;
- the exact effectuation boundary;
- and the atomic or crash-consistent transition that makes the operation effective.

The important question is therefore not:

> “Is OAuth used?”

or:

> “Is the OAuth Resource Server located near the final API?”

The engineering question is:

> **Does the component with mandatory control over the consequence independently establish that the exact pending effect is still authorized, under current protected state, immediately before that consequence is committed?**

---

## Three Different Security Questions

These mechanisms address related but different questions.

### 1. Who May Present the Authorization?

Mechanisms such as sender-constrained tokens, proof of possession, mTLS, DPoP, workload identity, or hardware-bound credentials can establish that the presenter possesses an expected key or protected identity.

This helps prevent simple token theft and unauthorized presentation.

But proving who presents an authorization does not by itself prove that the **actual pending consequence** is identical to the operation that was authorized.

---

### 2. What Was Authorized?

OAuth scopes, structured authorization details, transaction-specific parameters, policy objects, capabilities, or signed authorization records can describe what a principal is allowed to request.

For example:

```text
SEND
resource = file-A
destination = alice@example.com
application = messaging-service
```

This can provide strong and precise authorization semantics.

But a precise authorization object does not by itself establish that the component about to perform the operation has independently reconstructed the actual pending effect and compared it with the authorized effect.

---

### 3. What Is Actually About to Become Effective Now?

Execution finality addresses this third question.

Immediately before effectuation, the enforcement boundary must determine the real operation that will occur.

For example:

```text
Authorized operation:

SEND(
    resource = file-A,
    destination = alice@example.com
)
```

The actual operation reconstructed at the effectuation boundary must still be:

```text
Actual pending operation:

SEND(
    resource = file-A,
    destination = alice@example.com
)
```

If an intermediate component changes the destination:

```text
SEND(
    resource = file-A,
    destination = attacker@example.com
)
```

the final boundary must independently detect the mismatch and refuse effectuation.

The security property therefore depends not merely on an authorization check, but on **authorization-to-effect equality at commit time**.

---

# OAuth at the Final Boundary: What It Does and Does Not Establish

Consider the following arrangement:

```text
AI Agent
   |
   v
OAuth Authorization
   |
   v
Sender-Constrained Token
   |
   v
OAuth Resource Server
   |
   v
Final / Irreversible Operation
```

This can be a strong design.

However, merely placing the Resource Server at the final boundary does not automatically establish all execution-finality properties.

Additional questions remain:

```text
Did the Resource Server reconstruct the exact pending effect?

Did it compare every security-relevant parameter with
the authorized operation?

Did it verify current protected policy and revocation state?

Did it detect generation or epoch changes?

Can the same authority be replayed?

Can two concurrent executions both consume the same authorization?

Is authorization consumption atomic with the effect?

What happens if the system crashes between authorization
consumption and external effectuation?

Can another execution path bypass this Resource Server?

Can an upstream component substitute the resource,
destination, amount, route, tool arguments, or execution context?

Are cumulative budgets or quotas checked against protected state?

Does uncertainty fail closed?
```

If these questions are not answered by enforceable mechanisms, the implementation may have strong OAuth security while still lacking the complete execution-finality invariant.

---

# Functional Comparison

| Security Property | OAuth / Delegated Authorization | Sender-Constrained or Non-Bearer Authorization | OAuth at Final Boundary | Execution-Finality Architecture |
|---|---|---|---|---|
| Principal authorization | Yes | Yes | Yes | Yes |
| Delegated access | Yes | Yes | Yes | May be used |
| Fine-grained authorization parameters | Possible | Possible | Possible | Required where consequential |
| Token theft resistance | Not inherent to bearer tokens | Yes | Possible | Authority must not be transferable outside its binding |
| Final-boundary enforcement | Not inherently required | Not inherently required | Yes by deployment choice | Required |
| Exact pending-effect reconstruction | Not inherently required | Not inherently required | Not guaranteed merely by placement | Required |
| Authorized-versus-actual comparison | Application dependent | Application dependent | Application dependent | Required |
| Current protected-state validation | Deployment dependent | Deployment dependent | Deployment dependent | Required where relevant |
| Revocation / epoch fencing at commit | Deployment dependent | Deployment dependent | Deployment dependent | Required where relevant |
| Replay/single-use protection | Optional/profile dependent | Improved but not necessarily single-use | Deployment dependent | Required for single-use authority |
| TOCTOU-resistant check-and-commit | Not inherently defined | Not inherently defined | Not implied by final placement | Required |
| Atomic or crash-consistent authority consumption | Not inherently defined | Not inherently defined | Not implied | Required where double effect is prohibited |
| Alternate-path closure / complete mediation | Outside ordinary token semantics | Outside ordinary token semantics | Must be separately engineered | Required |
| Fail-safe behavior under uncertainty | Deployment dependent | Deployment dependent | Deployment dependent | Required for protected effectuation |

The distinction is therefore not that OAuth is incompatible with execution finality.

The distinction is that **OAuth alone does not define the complete commit-time enforcement sequence.**

---

# When OAuth Becomes Functionally Equivalent

OAuth can absolutely be used as part of an execution-finality implementation.

Suppose an OAuth Resource Server is placed at the real effectuation boundary and performs the following operations:

```text
1. Receive the proposed operation.

2. Keep the operation non-effective.

3. Reconstruct the actual operation about to occur.

4. Verify the authorization artifact.

5. Verify sender / presenter binding.

6. Verify exact operation parameters.

7. Compare authorized operation with actual pending effect.

8. Verify current protected policy state.

9. Verify revocation state.

10. Verify generation / fencing epoch.

11. Verify freshness and replay state.

12. Verify quota or cumulative budget where applicable.

13. Verify that the authority is intended for this exact
    enforcement boundary.

14. Atomically consume the applicable authority or protected state.

15. Commit the external effect.

16. Reject the operation if any required value is absent,
    stale, mismatched, replayed, revoked, unverifiable,
    rolled back, or indeterminate.

17. Ensure that no alternate execution path can create
    the same protected effect without passing equivalent checks.
```

At that point, the implementation is no longer merely “OAuth placed close to the action.”

It is implementing the execution-finality pattern using OAuth as one of its authorization mechanisms.

The component could still be called:

```text
OAuth Resource Server
API Gateway
Policy Enforcement Point
Reference Monitor
Transaction Coordinator
Command Gate
Actuation Gate
Safety Interlock
Protected Service
Execution Controller
Hardware Security Monitor
Finality Sink
```

The component name does not determine architectural equivalence.

The **enforcement sequence does**.

---

# Functional-Equivalence Rule

A useful engineering test is:

```text
Different names
    +
different protocols
    +
different implementation packaging
    +
different industry vocabulary

do not create a different architecture

IF

the same mandatory functional enforcement sequence
is implemented at the consequence boundary.
```

Conversely:

```text
Using the words

"final boundary",
"non-bearer",
"proof of possession",
"transaction authorization",
or
"OAuth Resource Server"

does not establish execution finality

UNLESS

the required commit-time enforcement invariants
are actually implemented.
```

---

# Compact Architectural Expression

The distinction can be summarized as:

```text
OAuth_at_Final_Boundary
+ Sender_Constraint

        !=

Execution_Finality
```

unless the deployment additionally implements:

```text
Execution_Finality =

    Mandatory_Effectuation_Boundary

  + Exact_Act_Binding

  + Actual_Effect_Reconstruction

  + Authorized_vs_Actual_Comparison

  + Current_Protected_State_Check

  + Revocation_and_Generation_Fencing

  + Replay_and_Single_Use_Control

  + TOCTOU_Resistant_Check_and_Commit

  + Atomic_or_Crash_Consistent_Consumption

  + Aggregate_Budget_Enforcement
        where applicable

  + Complete_Mediation_of_Alternate_Paths

  + Fail_Safe_Uncertainty_Handling
```

---

# Example: AI Tool Invocation

Consider an AI assistant authorized to make a payment:

```text
amount      = EUR 100
recipient   = Merchant-A
account     = Account-X
purpose     = Invoice-123
```

An OAuth authorization server may issue precise authority for this transaction.

A sender-constrained token can prevent another party from simply stealing and presenting that token.

A Resource Server at the payment endpoint can verify both.

Execution finality adds the requirement that the payment effectuation boundary independently establishes that the transaction it is actually about to commit is still:

```text
EUR 100
to Merchant-A
from Account-X
for Invoice-123
```

and not:

```text
EUR 10,000
to Merchant-B
from Account-X
```

It must additionally determine, where applicable, that:

```text
the authorization has not been revoked;

the applicable policy epoch has not changed;

the transaction has not already been executed;

the spending budget remains available;

a concurrent request has not already consumed the authority;

the exact authority is intended for this payment boundary;

and no alternate payment path can bypass the check.
```

Only then does the transaction become effective.

---

# Why This Matters for AI and Agent Interoperability

The distinction becomes particularly important for AI agents because the component generating the operation may not be the component trusted to authorize its consequence.

An AI model may validly generate:

```text
send_email(...)
make_payment(...)
upload_file(...)
change_network_configuration(...)
invoke_cloud_tool(...)
operate_device(...)
schedule_workload(...)
release_model_output(...)
```

without being trusted with unconditional authority to make those actions externally effective.

The architecture therefore separates:

```text
ability to propose
```

from:

```text
authority to cause consequence.
```

OAuth, MCP authorization, workload identity, RAR, DPoP, capability systems, hardware-backed credentials, or other mechanisms may participate in establishing that authority.

Execution finality defines the additional requirement that the **actual resulting effect remains non-effective until the mandatory consequence boundary verifies the exact current authority for that exact effect.**

---

# Relationship to Existing Security Mechanisms

This architecture is intended to complement rather than replace:

- OAuth;
- Rich Authorization Requests;
- proof-of-possession mechanisms;
- sender-constrained tokens;
- workload identity;
- transaction tokens;
- capability systems;
- access-control systems;
- trusted execution environments;
- hardware security modules;
- attestation;
- reference monitors;
- policy enforcement points;
- API gateways;
- transaction coordinators;
- secure elements;
- safety interlocks;
- industrial command gates;
- operating-system sandboxing;
- and conventional authentication and authorization mechanisms.

These mechanisms can supply identity, authorization, evidence, protected state, cryptographic bindings, or implementation substrates.

The additional execution-finality question is always:

> **Immediately before the consequential transition becomes real, can the enforcement boundary independently establish that the exact pending effect still corresponds to current, valid, unconsumed, non-revoked authority—and prevent the effect otherwise?**

That is the architectural distinction.

---

## Core Principle

**Computation is not authority.**

A model, application, agent, OAuth client, orchestration system, scheduler, controller, or upstream service may compute, propose, prepare, or authorize an operation.

The operation becomes consequential only after the system controlling the actual effect independently establishes that the precise pending act is authorized under current protected conditions.

That transition—from **proposed or authorized** to **externally effective**—is the execution-finality boundary.

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


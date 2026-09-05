from __future__ import annotations

import hashlib
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from . import cbor, cose


class Denied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def key_thumbprint(key: Ed25519PublicKey) -> bytes:
    return digest(key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


@dataclass(frozen=True)
class CandidateAct:
    requester: str
    action: str
    resource_digest: bytes
    destination: str
    destination_app: str
    finality_sink: str
    boundary: str
    session_id: str
    user_intent_digest: bytes
    policy_version: int
    security_epoch: int
    revocation_epoch: int
    nonce: bytes
    issued_at: int
    expires_at: int
    act_id: str

    def encode(self) -> bytes:
        if self.action not in {"message.send", "file.export", "app.dispatch"}:
            raise Denied("unsupported_action")
        if len(self.resource_digest) != 32 or len(self.user_intent_digest) != 32 or len(self.nonce) < 16:
            raise Denied("invalid_binding")
        if not self.requester or not self.destination or not self.finality_sink or not self.boundary:
            raise Denied("missing_load_bearing_field")
        if self.expires_at <= self.issued_at or self.expires_at - self.issued_at > 300:
            raise Denied("invalid_validity_window")
        return cbor.dumps({1:1,2:self.act_id,3:self.requester,4:self.action,5:self.resource_digest,6:self.destination,7:self.destination_app,8:self.finality_sink,9:self.boundary,10:self.session_id,11:self.user_intent_digest,12:self.policy_version,13:self.security_epoch,14:self.revocation_epoch,15:self.nonce,16:self.issued_at,17:self.expires_at})

    @property
    def commitment(self) -> bytes:
        return digest(self.encode())


@dataclass(frozen=True)
class ActualEffect:
    requester: str
    action: str
    resource: bytes
    destination: str
    destination_app: str
    finality_sink: str
    boundary: str
    session_id: str
    user_intent_digest: bytes
    policy_version: int
    security_epoch: int
    revocation_epoch: int
    nonce: bytes
    issued_at: int
    expires_at: int
    act_id: str

    def reconstruct(self) -> CandidateAct:
        return CandidateAct(self.requester,self.action,digest(self.resource),self.destination,self.destination_app,self.finality_sink,self.boundary,self.session_id,self.user_intent_digest,self.policy_version,self.security_epoch,self.revocation_epoch,self.nonce,self.issued_at,self.expires_at,self.act_id)


@dataclass(frozen=True)
class PolicyState:
    version: int
    security_epoch: int
    revocation_epoch: int
    allowed_actions: frozenset[str]
    allowed_destination_apps: frozenset[str]


@dataclass(frozen=True)
class AuthorityBundle:
    lavr: bytes
    capability: bytes


class ProtectedState:
    """Crash-consistent local authority/effect store.

    SQLite models a protected OS database. A platform implementation must map
    this boundary to rollback-protected storage or an equivalent trusted
    service; SQLite alone is not a hardware trust anchor.
    """
    def __init__(self, path: str):
        self.db=sqlite3.connect(path,check_same_thread=False,isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL"); self.db.execute("PRAGMA synchronous=FULL"); self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS issued(cap_id BLOB PRIMARY KEY, act_id TEXT NOT NULL, nonce BLOB NOT NULL UNIQUE, requester TEXT NOT NULL, expires INTEGER NOT NULL, state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS revoked(subject TEXT PRIMARY KEY, epoch INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS effects(act_id TEXT PRIMARY KEY, action TEXT NOT NULL, destination TEXT NOT NULL, resource BLOB NOT NULL, committed_at INTEGER NOT NULL);
        """)
        self.lock=threading.Lock()

    def record_issued(self, cap_id: bytes, act: CandidateAct) -> None:
        with self.lock:
            try: self.db.execute("INSERT INTO issued VALUES(?,?,?,?,?,'ISSUED')",(cap_id,act.act_id,act.nonce,act.requester,act.expires_at))
            except sqlite3.IntegrityError as exc: raise Denied("nonce_or_act_reuse") from exc

    def revoke(self, subject: str, epoch: int) -> None:
        with self.lock: self.db.execute("INSERT INTO revoked VALUES(?,?) ON CONFLICT(subject) DO UPDATE SET epoch=max(epoch,excluded.epoch)",(subject,epoch))

    def is_revoked(self, subject: str, capability_epoch: int) -> bool:
        row=self.db.execute("SELECT epoch FROM revoked WHERE subject=?",(subject,)).fetchone()
        return bool(row and row[0] >= capability_epoch)

    def finalize(self, cap_id: bytes, effect: ActualEffect, current: PolicyState, now: int) -> None:
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row=self.db.execute("SELECT state,requester,expires FROM issued WHERE cap_id=?",(cap_id,)).fetchone()
                if not row or row[0] != "ISSUED": raise Denied("authority_consumed_or_unknown")
                if now > row[2]: raise Denied("authority_expired")
                revoked=self.db.execute("SELECT epoch FROM revoked WHERE subject=?",(row[1],)).fetchone()
                if revoked and revoked[0] >= current.revocation_epoch: raise Denied("authority_revoked")
                if (effect.policy_version,effect.security_epoch,effect.revocation_epoch)!=(current.version,current.security_epoch,current.revocation_epoch): raise Denied("stale_governance_state")
                self.db.execute("UPDATE issued SET state='COMMITTING' WHERE cap_id=? AND state='ISSUED'",(cap_id,))
                self.db.execute("INSERT INTO effects VALUES(?,?,?,?,?)",(effect.act_id,effect.action,effect.destination,effect.resource,now))
                self.db.execute("UPDATE issued SET state='EFFECT_COMMITTED' WHERE cap_id=?",(cap_id,))
                self.db.execute("UPDATE issued SET state='CONSUMED' WHERE cap_id=?",(cap_id,))
                self.db.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                self.db.execute("ROLLBACK"); raise Denied("duplicate_effect") from exc
            except Exception:
                self.db.execute("ROLLBACK"); raise

    def effect_count(self) -> int:
        return int(self.db.execute("SELECT count(*) FROM effects").fetchone()[0])


class ProtectedValidator:
    def __init__(self, signing_key: Ed25519PrivateKey, kid: bytes, state: ProtectedState, policy: PolicyState, requester_keys: dict[str,Ed25519PublicKey]):
        self.key,self.kid,self.state,self.policy,self.requester_keys=signing_key,kid,state,policy,requester_keys

    def prepare(self, act: CandidateAct, user_intent_verified: bool, now: int | None=None) -> AuthorityBundle:
        now=int(time.time()) if now is None else now
        if act.requester not in self.requester_keys: raise Denied("unknown_requester")
        if act.action not in self.policy.allowed_actions or act.destination_app not in self.policy.allowed_destination_apps: raise Denied("policy_denied")
        if not user_intent_verified: raise Denied("user_intent_not_verified")
        if (act.policy_version,act.security_epoch,act.revocation_epoch)!=(self.policy.version,self.policy.security_epoch,self.policy.revocation_epoch): raise Denied("stale_governance_state")
        if now < act.issued_at-5 or now > act.expires_at: raise Denied("candidate_expired")
        if self.state.is_revoked(act.requester,act.revocation_epoch): raise Denied("requester_revoked")
        commitment=act.commitment; receipt_id=secrets.token_bytes(16)
        lavr_payload=cbor.dumps({1:1,2:receipt_id,3:commitment,4:act.requester,5:act.nonce,6:act.policy_version,7:act.security_epoch,8:act.revocation_epoch,9:act.finality_sink,10:act.boundary,11:now,12:["requester","scope","resource","destination","user-intent","policy","freshness","revocation"]})
        lavr=cose.sign1(lavr_payload,self.key,self.kid); cap_id=secrets.token_bytes(16)
        capability_payload=cbor.dumps({1:1,2:cap_id,3:commitment,4:digest(lavr),5:act.requester,6:key_thumbprint(self.requester_keys[act.requester]),7:act.finality_sink,8:act.boundary,9:act.nonce,10:act.policy_version,11:act.security_epoch,12:act.revocation_epoch,13:now,14:act.expires_at,15:1})
        capability=cose.sign1(capability_payload,self.key,self.kid)
        self.state.record_issued(cap_id,act)
        return AuthorityBundle(lavr,capability)


def create_presentation(capability: bytes, effect: ActualEffect, requester_key: Ed25519PrivateKey, kid: bytes) -> bytes:
    payload=cbor.dumps({1:digest(capability),2:effect.reconstruct().commitment,3:effect.act_id,4:effect.nonce})
    return cose.sign1(payload,requester_key,kid)


class FinalitySink:
    def __init__(self, sink_id: str, boundary: str, validator_keys: dict[bytes,Ed25519PublicKey], requester_keys: dict[bytes,Ed25519PublicKey], state: ProtectedState, policy: PolicyState):
        self.sink_id,self.boundary,self.validator_keys,self.requester_keys,self.state,self.policy=sink_id,boundary,validator_keys,requester_keys,state,policy

    def finalize(self, effect: ActualEffect, bundle: AuthorityBundle, presentation: bytes, now: int | None=None) -> str:
        now=int(time.time()) if now is None else now
        try:
            lavr_raw,_=cose.verify1(bundle.lavr,self.validator_keys); cap_raw,_=cose.verify1(bundle.capability,self.validator_keys)
            lavr=cbor.loads(lavr_raw); cap=cbor.loads(cap_raw)
        except ValueError as exc: raise Denied("invalid_authority_signature") from exc
        if cap[4]!=digest(bundle.lavr) or lavr[3]!=cap[3]: raise Denied("lavr_binding_mismatch")
        if cap[7]!=self.sink_id or cap[8]!=self.boundary or (effect.finality_sink,effect.boundary)!=(self.sink_id,self.boundary): raise Denied("wrong_finality_boundary")
        if now > cap[14]: raise Denied("authority_expired")
        actual=effect.reconstruct().commitment
        if actual!=cap[3] or actual!=lavr[3]: raise Denied("actual_effect_mismatch")
        try:
            pop_raw,pop_kid=cose.verify1(presentation,self.requester_keys); pop=cbor.loads(pop_raw)
        except ValueError as exc: raise Denied("invalid_proof_of_possession") from exc
        if key_thumbprint(self.requester_keys[pop_kid])!=cap[6] or pop!={1:digest(bundle.capability),2:actual,3:effect.act_id,4:effect.nonce}: raise Denied("proof_of_possession_mismatch")
        if self.state.is_revoked(effect.requester,self.policy.revocation_epoch): raise Denied("authority_revoked")
        self.state.finalize(cap[2],effect,self.policy,now)
        return "EFFECT_COMMITTED"


from __future__ import annotations

import tempfile
import time
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from interoperability.core import ActualEffect, CandidateAct, Denied, FinalitySink, PolicyState, ProtectedState, ProtectedValidator, create_presentation


NOW=1_800_000_000
RESOURCE=b"confidential tax return bytes"


class InteroperabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.NamedTemporaryFile(); self.state=ProtectedState(self.tmp.name)
        self.os_key=Ed25519PrivateKey.generate(); self.app_key=Ed25519PrivateKey.generate(); self.other_key=Ed25519PrivateKey.generate()
        self.policy=PolicyState(7,11,3,frozenset({"message.send"}),frozenset({"system.messages"}))
        self.act=CandidateAct("assistant.example","message.send",__import__('hashlib').sha256(RESOURCE).digest(),"alice@example.com","system.messages","urn:device:sink:messages","messages-send-boundary","session-123",bytes.fromhex("aa"*32),7,11,3,bytes.fromhex("bb"*24),NOW,NOW+30,"act-123")
        self.validator=ProtectedValidator(self.os_key,b"os-validator-1",self.state,self.policy,{"assistant.example":self.app_key.public_key()})
        self.bundle=self.validator.prepare(self.act,True,NOW)
        self.effect=ActualEffect("assistant.example","message.send",RESOURCE,"alice@example.com","system.messages","urn:device:sink:messages","messages-send-boundary","session-123",bytes.fromhex("aa"*32),7,11,3,bytes.fromhex("bb"*24),NOW,NOW+30,"act-123")
        self.sink=FinalitySink("urn:device:sink:messages","messages-send-boundary",{b"os-validator-1":self.os_key.public_key()},{b"assistant-key-1":self.app_key.public_key(),b"attacker-key":self.other_key.public_key()},self.state,self.policy)

    def tearDown(self):
        self.state.db.close(); self.tmp.close()

    def presentation(self,effect=None,key=None,kid=b"assistant-key-1"):
        return create_presentation(self.bundle.capability,effect or self.effect,key or self.app_key,kid)

    def test_exact_effect_commits_once(self):
        self.assertEqual(self.sink.finalize(self.effect,self.bundle,self.presentation(),NOW),"EFFECT_COMMITTED")
        self.assertEqual(self.state.effect_count(),1)
        with self.assertRaises(Denied): self.sink.finalize(self.effect,self.bundle,self.presentation(),NOW)
        self.assertEqual(self.state.effect_count(),1)

    def test_recipient_substitution(self):
        changed=ActualEffect(**{**self.effect.__dict__,"destination":"attacker@evil.example"})
        with self.assertRaisesRegex(Denied,"actual_effect_mismatch"): self.sink.finalize(changed,self.bundle,self.presentation(changed),NOW)

    def test_resource_substitution(self):
        changed=ActualEffect(**{**self.effect.__dict__,"resource":b"different file"})
        with self.assertRaisesRegex(Denied,"actual_effect_mismatch"): self.sink.finalize(changed,self.bundle,self.presentation(changed),NOW)

    def test_stolen_capability_without_app_key(self):
        stolen=self.presentation(key=self.other_key,kid=b"attacker-key")
        with self.assertRaisesRegex(Denied,"proof_of_possession_mismatch"): self.sink.finalize(self.effect,self.bundle,stolen,NOW)

    def test_wrong_sink(self):
        wrong=ActualEffect(**{**self.effect.__dict__,"finality_sink":"urn:device:sink:files"})
        with self.assertRaisesRegex(Denied,"wrong_finality_boundary"): self.sink.finalize(wrong,self.bundle,self.presentation(wrong),NOW)

    def test_revocation_after_issuance(self):
        self.state.revoke("assistant.example",3)
        with self.assertRaisesRegex(Denied,"authority_revoked"): self.sink.finalize(self.effect,self.bundle,self.presentation(),NOW)

    def test_policy_epoch_change_after_issuance(self):
        new_policy=PolicyState(8,12,4,self.policy.allowed_actions,self.policy.allowed_destination_apps)
        sink=FinalitySink(self.sink.sink_id,self.sink.boundary,self.sink.validator_keys,self.sink.requester_keys,self.state,new_policy)
        with self.assertRaisesRegex(Denied,"stale_governance_state"): sink.finalize(self.effect,self.bundle,self.presentation(),NOW)

    def test_user_intent_required(self):
        act=CandidateAct(**{**self.act.__dict__,"nonce":bytes.fromhex("cc"*24),"act_id":"act-456"})
        with self.assertRaisesRegex(Denied,"user_intent_not_verified"): self.validator.prepare(act,False,NOW)

    def test_first_and_third_party_use_same_predicates(self):
        first_key=Ed25519PrivateKey.generate()
        validator=ProtectedValidator(self.os_key,b"os-validator-1",self.state,self.policy,{"system.assistant":first_key.public_key()})
        act=CandidateAct(**{**self.act.__dict__,"requester":"system.assistant","nonce":bytes.fromhex("dd"*24),"act_id":"act-system"})
        bundle=validator.prepare(act,True,NOW)
        effect=ActualEffect(**{**self.effect.__dict__,"requester":"system.assistant","nonce":act.nonce,"act_id":act.act_id})
        sink=FinalitySink(self.sink.sink_id,self.sink.boundary,self.sink.validator_keys,{b"system-key":first_key.public_key()},self.state,self.policy)
        pop=create_presentation(bundle.capability,effect,first_key,b"system-key")
        self.assertEqual(sink.finalize(effect,bundle,pop,NOW),"EFFECT_COMMITTED")


if __name__=="__main__": unittest.main()


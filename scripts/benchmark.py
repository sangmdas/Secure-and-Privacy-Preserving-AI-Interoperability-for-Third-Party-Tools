from __future__ import annotations
import hashlib,platform,statistics,sys,tempfile,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from interoperability.core import *

def measure(name,fn,n=10000):
    for _ in range(500): fn()
    samples=[]
    for _ in range(n):
        start=time.perf_counter_ns(); fn(); samples.append((time.perf_counter_ns()-start)/1000)
    samples.sort(); p=lambda x:samples[min(n-1,int(n*x))]
    print(f"{name}: n={n} median={statistics.median(samples):.2f}us p95={p(.95):.2f}us p99={p(.99):.2f}us")

now=int(time.time()); os_key=Ed25519PrivateKey.generate(); app_key=Ed25519PrivateKey.generate(); resource=b"x"*4096
policy=PolicyState(1,1,1,frozenset({"message.send"}),frozenset({"system.messages"}))
def make_act(i=0): return CandidateAct("assistant.example","message.send",hashlib.sha256(resource).digest(),"alice@example.com","system.messages","urn:sink:messages","send-boundary","session",b"i"*32,1,1,1,(i.to_bytes(8,"big")+b"n"*16),now,now+60,f"act-{i}")
tmp=tempfile.NamedTemporaryFile(); state=ProtectedState(tmp.name); validator=ProtectedValidator(os_key,b"os-1",state,policy,{"assistant.example":app_key.public_key()})
act=make_act(); bundle=validator.prepare(act,True,now); effect=ActualEffect("assistant.example","message.send",resource,"alice@example.com","system.messages","urn:sink:messages","send-boundary","session",b"i"*32,1,1,1,act.nonce,now,now+60,"act-0")
sink=FinalitySink("urn:sink:messages","send-boundary",{b"os-1":os_key.public_key()},{b"app-1":app_key.public_key()},state,policy); pop=create_presentation(bundle.capability,effect,app_key,b"app-1")
print(f"platform={platform.platform()} python={platform.python_version()} resource_bytes={len(resource)} samples=10000 concurrency=1")
measure("CandidateAct encode+commitment",lambda:make_act().commitment)
i=iter(range(1,20000)); measure("LAVR+capability issuance",lambda:validator.prepare(make_act(next(i)),True,now))
measure("proof-of-possession creation",lambda:create_presentation(bundle.capability,effect,app_key,b"app-1"))
cycle_samples=[]
for j in range(30000,31000):
    a=make_act(j); b=validator.prepare(a,True,now)
    e=ActualEffect("assistant.example","message.send",resource,"alice@example.com","system.messages","urn:sink:messages","send-boundary","session",b"i"*32,1,1,1,a.nonce,now,now+60,a.act_id)
    p=create_presentation(b.capability,e,app_key,b"app-1")
    start=time.perf_counter_ns(); sink.finalize(e,b,p,now); cycle_samples.append((time.perf_counter_ns()-start)/1000)
cycle_samples.sort(); q=lambda x:cycle_samples[min(999,int(1000*x))]
print(f"stateful Finality Sink verify+SQLite commit: n=1000 median={statistics.median(cycle_samples):.2f}us p95={q(.95):.2f}us p99={q(.99):.2f}us")

import os, json, time, re, sys, subprocess, shutil
from pathlib import Path

os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['TRANSFORMERS_NO_FLAX'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['VLLM_NO_USAGE_STATS'] = '1'
os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'
os.environ['VLLM_ENGINE_READY_TIMEOUT_S'] = '1200'
os.environ['NCCL_DEBUG'] = 'WARN'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
os.environ['LITELLM_TELEMETRY'] = 'False'
os.environ['OTEL_SDK_DISABLED'] = 'true'
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'EMPTY')
os.environ['LOCAL_API_KEY'] = os.environ.get('LOCAL_API_KEY', 'EMPTY')


import glob as _glob, importlib as _importlib
print('INPUT DIRS:', os.listdir('/kaggle/input') if os.path.isdir('/kaggle/input') else 'NA')
try:
    print('INPUT datasets:', os.listdir('/kaggle/input/datasets'))
except Exception as e:
    print('no datasets dir', e)

# Step 1: downgrade torch to 2.10.0 from helper kernel (compatible with vLLM 0.19.1)
import glob as _g_torch
_extra_dir = '/kaggle/input/g4-torch-wheel-cache/extra_wheels'
_torch_wheels = _g_torch.glob(_extra_dir + '/torch-2.10.0*.whl')
print('torch 2.10.0 wheels found:', _torch_wheels)
if _torch_wheels:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-index', '--no-deps', '--force-reinstall', _torch_wheels[0]], check=False)
    print('torch install done')
# install all cp313 helper wheels (xgrammar, msgspec, cbor2, etc.)
import glob as _g_all
_allw = sorted(_g_all.glob(_extra_dir + '/*.whl'))
print('extra wheels to install:', len(_allw))
for _w in _allw:
    if 'torch-2.10.0' in _w:
        continue
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-index', '--no-deps', '--force-reinstall', _w], check=False)
print('extra wheels install done')

WHEELHOUSE_CANDIDATES = [
    Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse'),
    Path('/kaggle/input/gemma-4-developer-agent-wheelhouse'),
    Path('/kaggle/input/gemma-4-developer-agent/wheels'),
    DATA_DIR / 'wheels' if 'DATA_DIR' in globals() else Path('/kaggle/input/competitions/gemma-4-developer-agent/wheels'),
]
WHEELHOUSE_DIR = None
for c in WHEELHOUSE_CANDIDATES:
    if c.exists():
        WHEELHOUSE_DIR = c
        break
print('Wheelhouse candidate selected:', WHEELHOUSE_DIR)
try:
    if WHEELHOUSE_DIR is not None and WHEELHOUSE_DIR.exists():
        for pth_pattern in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth','/usr/local/lib/python*/site-packages/*cutlass*.pth'):
            for pth in _glob.glob(pth_pattern):
                try: os.unlink(pth)
                except OSError: pass
        tmp_whl = Path('/tmp/wheelhouse')
        tmp_whl.mkdir(parents=True, exist_ok=True)
        for w in WHEELHOUSE_DIR.glob('*.whl'):
            if 'cutlass' in w.name.lower():
                continue
            target_name = w.name.replace('cu128','+cu128') if ('cu128' in w.name and '+' not in w.name) else w.name
            target = tmp_whl / target_name
            if not target.exists():
                try: os.symlink(w, target)
                except FileExistsError: pass
        needed = ['swegemma', 'adk_submission', 'adk_eval_core', 'vllm']
        wheels = []
        for w in sorted(tmp_whl.glob('*.whl')):
            if any(n in w.name for n in needed):
                wheels.append(str(w))
        print(f'Installing {len(wheels)} needed wheels from {WHEELHOUSE_DIR}...')
        subprocess.run([sys.executable,'-m','pip','install','-q','--no-deps','--force-reinstall',*wheels], check=False)
        _importlib.invalidate_caches()
        print('Wheelhouse installation complete.')
        # verify
        import torch as _t, vllm as _v
        print('SUCCESS:', _t.__version__, _v.__version__)
except Exception as _e:
    print('Wheel install skipped/failed:', repr(_e))

DATA_DIR = Path('/kaggle/input/competitions/gemma-4-developer-agent')
WORKING_DIR = Path('/kaggle/working')
WORKING_DIR.mkdir(parents=True, exist_ok=True)

# Best-effort offline wheel install
def _ensure_imports():
    try:
        import swegemma, adk_submission  # noqa
        print('Imports already available')
        return
    except Exception as e:
        print('Import missing:', repr(e))
    find_links = []
    for c in WHEELHOUSE_CANDIDATES:
        if c.exists():
            find_links.append(str(c))
    # also glob
    for root in ['/kaggle/input']:
        for dirpath, dirnames, filenames in os.walk(root):
            if any(f.endswith('.whl') for f in filenames):
                find_links.append(dirpath)
    find_links = list(dict.fromkeys(find_links))
    print('find_links:', find_links)
    cmd = [sys.executable, '-m', 'pip', 'install', '-q', '--no-index']
    for fl in find_links:
        cmd += ['--find-links', fl]
    cmd += ['swegemma', 'adk_submission', 'adk-eval-core', 'adk_eval_core']
    print('Running:', ' '.join(cmd))
    r = subprocess.run(cmd, check=False, capture_output=True, text=True)
    print('pip rc:', r.returncode)
    print('pip stdout:', r.stdout[-1000:])
    print('pip stderr:', r.stderr[-1000:])
    _importlib.invalidate_caches()
_ensure_imports()

import asyncio, concurrent.futures
import yaml
import torch
import litellm
from adk_submission import VllmConfig, VllmServer, discover_adapters
from adk_submission.discovery import discover_declared_models
from swegemma.config import EvalConfig, build_submission_limits
from swegemma.evaluate import Evaluator

litellm.drop_params = True

MODEL_NAME = 'gemma-4-31b-it-qat-w4a16-ct'
MODEL_PATH = Path(f'/kaggle/input/models/google/gemma-4/other/{MODEL_NAME}/2')
assert MODEL_PATH.exists(), f'Model weights not found at {MODEL_PATH}'

# Locate bundle dirs
def find_bundle(name):
    mapping = {'exp05': 'exp05_patch_integrity', 'exp10-consolidated': 'exp10_consolidated'}
    dname = mapping.get(name, name)
    root = _materialize_bundles()
    cand = root / dname
    if (cand / 'agent.yaml').exists():
        return cand
    raise FileNotFoundError(name)

EMBEDDED_BUNDLES = {'exp05_patch_integrity': {'agent.yaml': 'bmFtZTogc3dlX2FnZW50Cm1vZGVsOiBnZW1tYS00LTMxYi1pdC1xYXQtdzRhMTYtY3QKaW5zdHJ1Y3Rpb246ICFpbmNsdWRlIHByb21wdHMvc3lzdGVtLm1kCnRvb2xzOgogIC0gcnVuX2NvbW1hbmQKICAtIHJlYWRfZmlsZQogIC0gZWRpdF9maWxlCiAgLSB3cml0ZV9maWxlCiAgLSBnZXRfc3RhdHVzCiAgLSBzdWJtaXRfcGF0Y2gKICAtIGdldF9jb2RlX25laWdoYm9ycwogIC0gc2VhcmNoX3NpbWlsYXJfY29kZQogIC0gZ2V0X2NvZGVfc3ViZ3JhcGgKZ2VuZXJhdGVfY29udGVudF9jb25maWc6ICFpbmNsdWRlIGNvbmZpZ3Mvc2FtcGxpbmcueWFtbAo=', 'eval_config.yaml': 'ZXZhbHVhdGlvbjoKICB0aW1lb3V0X3NlY29uZHM6IDI0MAogIG1heF90b29sX2NhbGxzOiAyOAogIG1heF90aW1lX21pbnV0ZXM6IDgKICBtYXhfdHVybnM6IDgwCg==', 'configs/sampling.yaml': 'dGVtcGVyYXR1cmU6IDAuMgp0b3BfcDogMC45NQptYXhfb3V0cHV0X3Rva2VuczogODE5Mgp0aGlua2luZ19jb25maWc6CiAgdGhpbmtpbmdfYnVkZ2V0OiA0MDk2CiAgaW5jbHVkZV90aG91Z2h0czogdHJ1ZQo=', 'prompts/system.md': 'WW91IGFyZSBhbiBhdXRvbm9tb3VzIHNvZnR3YXJlIGVuZ2luZWVyLiBZb3VyIGpvYjogbWFrZSB0aGUgc21hbGxlc3QgY29ycmVjdCBjaGFuZ2UgdG8gdGhlIFNPVVJDRSBjb2RlIGluIC93b3Jrc3BhY2Ugc28gdGhhdCB0aGUgaGlkZGVuIHRlc3RzIGZvciB0aGUgaXNzdWUgYmVsb3cgcGFzcy4gVGhlIGhpZGRlbiB0ZXN0cyB3ZXJlIHdyaXR0ZW4gZnJvbSB0aGUgaXNzdWUgdGV4dCwgc28gdGhlIGV4YWN0IG5hbWVzLCBtZXNzYWdlcywgdHlwZXMgYW5kIGJlaGF2aW91cnMgaW4gdGhlIGlzc3VlIGFyZSB0aGUgc3BlY2lmaWNhdGlvbi4KCiMgSEFSRCBMSU1JVFMKLSAyOCB0b29sIGNhbGxzIGFuZCA4IG1pbnV0ZXMgaW4gdG90YWwuIFdoZW4gZWl0aGVyIHJ1bnMgb3V0LCB0aGUgd29ya2luZyB0cmVlIGlzIGdyYWRlZCBhcyBpdCBpcy4gQW4gZWRpdCB0aGF0IGV4aXN0cyBjb3VudHMsIGV2ZW4gaWYgeW91IG5ldmVyIGNhbGwgYHN1Ym1pdF9wYXRjaGAuIEFuIHVuZWRpdGVkIHRyZWUgYWx3YXlzIHNjb3JlcyB6ZXJvLgotIE5ldmVyIGNyZWF0ZSwgbW9kaWZ5IG9yIGRlbGV0ZSB0ZXN0IGZpbGVzIChgdGVzdF8qLnB5YCwgYCpfdGVzdC5weWAsIGFueXRoaW5nIHVuZGVyIGB0ZXN0cy9gKS4gVGhpcyBpcyBhbiBhdXRvbWF0aWMgZmFpbHVyZS4KLSBOZXZlciBydW4gYSBmdWxsIHRlc3Qgc3VpdGUgKGJhcmUgYHB5dGVzdGAsIGBweXRlc3QgLmAsIGB1bml0dGVzdCBkaXNjb3ZlcmApLiBBbHdheXMgbmFtZSBvbmUgdGVzdCBmaWxlLCBhbmQgYWRkIGAta2Agd2hlbiB5b3UgY2FuLgotIE5ldmVyIGxvb2sgb3V0c2lkZSAvd29ya3NwYWNlLiBBbGwgZGVwZW5kZW5jaWVzIGFyZSBhbHJlYWR5IGluc3RhbGxlZC4KLSBOZXZlciB1c2UgYHNlYXJjaF9zaW1pbGFyX2NvZGVgLCBgZ2V0X2NvZGVfbmVpZ2hib3JzYCBvciBgZ2V0X2NvZGVfc3ViZ3JhcGhgLiBUaGV5IHJldHVybiBub3RoaW5nIHVzZWZ1bC4KCiMgQ0FMTCBQTEFOCi0gQ2FsbHMgMS04OiBsb2NhdGUgYW5kIHJlYWQuIENhbGxzIDktMTI6IGVkaXQuIFlvdSBNVVNUIGhhdmUgZWRpdGVkIGEgc291cmNlIGZpbGUgYnkgY2FsbCAxMi4gSWYgeW91IGFyZSB1bnN1cmUsIG1ha2UgeW91ciBiZXN0LWd1ZXNzIGVkaXQgaW4gdGhlIG1vc3QgbGlrZWx5IHBsYWNlIG5vdy4gQSB3cm9uZyBlZGl0IGNhbiBzdGlsbCBiZSBjb3JyZWN0ZWQuIFB1cmUgcmVhZGluZyBjYW5ub3Qgc2NvcmUuCi0gQ2FsbHMgMTMtMjA6IHZlcmlmeSBhbmQgY29ycmVjdC4KLSBDYWxsIDIwIG9ud2FyZDogbm8gbmV3IGV4cGxvcmF0aW9uLiBDaGVjaywgZml4LCBzdWJtaXQuCi0gQWx3YXlzIGZpbmlzaCB3aXRoIGBnaXQgZGlmZmAgZm9sbG93ZWQgYnkgYHN1Ym1pdF9wYXRjaGAuCgojIFBST0NFRFVSRQoKIyMgMS4gRXh0cmFjdCB0aGUgc3BlY2lmaWNhdGlvbiAobm8gdG9vbCBjYWxsKQpGcm9tIHRoZSBpc3N1ZSwgbGlzdCBmb3IgeW91cnNlbGY6IHRoZSBleGFjdCBmaWxlLCBmdW5jdGlvbiwgY2xhc3Mgb3IgQ0xJIG5hbWU7IHRoZSBleGFjdCBlcnJvciBtZXNzYWdlIGFuZCBleGNlcHRpb24gdHlwZTsgdGhlIGV4cGVjdGVkIHJldHVybiB2YWx1ZSBvciBvdXRwdXQ7IHRoZSBpbnB1dHMgdGhhdCB0cmlnZ2VyIHRoZSBidWc7IGV2ZXJ5IGVkZ2UgY2FzZSBtZW50aW9uZWQgKE5vbmUsIGVtcHR5LCBuZWdhdGl2ZSwgdW5pY29kZSwgZHVwbGljYXRlcywgZGVmYXVsdHMpLiBUcmVhdCBldmVyeSBjb25jcmV0ZSBzdHJpbmcgYW5kIG5hbWUgaW4gdGhlIGlzc3VlIGFzIGEgbGl0ZXJhbCB0aGF0IG11c3QgYXBwZWFyIGV4YWN0bHkgaW4geW91ciBjb2RlLgoKIyMgMi4gTG9jYXRlCi0gVXNlIHRoZSBwYXRocyBhbmQgc3ltYm9scyBmcm9tIHRoZSBpc3N1ZSBkaXJlY3RseS4gSWYgdGhlcmUgaXMgbm8gcGF0aCwgcnVuIG9uZSBzZWFyY2g6IGBnaXQgZ3JlcCAtbiAibW9zdCBzcGVjaWZpYyBzdHJpbmcgb3IgaWRlbnRpZmllciIgLS0gJyoucHknIHwgaGVhZCAtMjBgLgotIFVzZSBgcmVhZF9maWxlYCBvbiB0aGUgcmVsZXZhbnQgcmVnaW9uIChhYm91dCA0MCBsaW5lcyBhcm91bmQgdGhlIHRhcmdldCkgYW5kIG5vdCB3aG9sZSBmaWxlcy4KLSBGb3IgYSBidWc6IGZpbmQgd2hlcmUgdGhlIHdyb25nIGJlaGF2aW91ciBpcyBwcm9kdWNlZCwgdGhlbiBjaGVjayBob3cgY2FsbGVycyB1c2UgaXQgd2l0aCBvbmUgYGdpdCBncmVwIC1uICJmdW5jdGlvbl9uYW1lIiAtLSAnKi5weScgfCBoZWFkYC4KLSBGb3IgYSBmZWF0dXJlOiBmaW5kIHRoZSBjbG9zZXN0IGV4aXN0aW5nIHNpYmxpbmcgKGEgc2ltaWxhciBmdW5jdGlvbiwgb3B0aW9uLCBjbGFzcywgb3IgZG9jIGV4YW1wbGUpIGFuZCBjb3B5IGl0cyBwYXR0ZXJuLiBUaGF0IHBhdHRlcm4gaW5jbHVkZXMgcmVnaXN0cmF0aW9uIHBvaW50cyBzdWNoIGFzIGBfX2FsbF9fYCwgb3B0aW9uIGxpc3RzLCBkaXNwYXRjaCB0YWJsZXMsIGFuZCBpbXBvcnRzLgotIElmIHRoZSBpc3N1ZSBpbmNsdWRlcyBhIGNvZGUgc25pcHBldCB0aGF0IHJlcHJvZHVjZXMgdGhlIHByb2JsZW0sIHlvdSBtYXkgcnVuIGl0IG9uY2Ugd2l0aCBgcHl0aG9uIC1jYCAob25lIGNhbGwsIG5ldmVyIGNyZWF0ZSBhIGZpbGUpIHRvIHNlZSB0aGUgcmVhbCBlcnJvci4KCiMjIDMuIEVkaXQKLSBVc2UgYGVkaXRfZmlsZWAgZm9yIGNoYW5nZXMgdG8gZXhpc3RpbmcgY29kZS4gVXNlIGB3cml0ZV9maWxlYCBvbmx5IGZvciBhIGdlbnVpbmVseSBuZXcgc291cmNlIGZpbGUgdGhhdCB0aGUgaXNzdWUgcmVxdWlyZXMuCi0gRml4IHRoZSBjYXVzZSwgbm90IHRoZSBzeW1wdG9tLiBEbyBub3Qgc3BlY2lhbC1jYXNlIHRoZSBleGFtcGxlIGZyb20gdGhlIGlzc3VlLgotIENoYW5nZSBvbmx5IHdoYXQgdGhlIGlzc3VlIHJlcXVpcmVzLiBLZWVwIGV4aXN0aW5nIHNpZ25hdHVyZXMsIGRlZmF1bHRzLCBhbmQgYmFja3dhcmQgY29tcGF0aWJpbGl0eSB1bmxlc3MgdGhlIGlzc3VlIHNheXMgb3RoZXJ3aXNlLiBNYXRjaCB0aGUgc3R5bGUsIG5hbWluZyBhbmQgZXJyb3ItaGFuZGxpbmcgaWRpb21zIG9mIHRoZSBzdXJyb3VuZGluZyBjb2RlLgotIFVzZSB0aGUgZXhhY3QgZXhjZXB0aW9uIGNsYXNzIGFuZCBleGFjdCBtZXNzYWdlIHRleHQgZnJvbSB0aGUgaXNzdWUuIElmIHRoZSBpc3N1ZSBvbmx5IGRlc2NyaWJlcyB0aGUgZXJyb3IsIHJldXNlIHRoZSB3b3JkaW5nIHN0eWxlIG9mIG5laWdoYm91cmluZyBlcnJvciBtZXNzYWdlcy4KLSBIYW5kbGUgZXZlcnkgZWRnZSBjYXNlIHlvdSBsaXN0ZWQgaW4gc3RlcCAxLgotIEZvciBkb2N1bWVudGF0aW9uLWNvZGUgdGFza3MgKGZvciBleGFtcGxlIEZhc3RBUEkpLCBlZGl0IHRoZSBleGVjdXRhYmxlIGNvZGUgdW5kZXIgYGRvY3Nfc3JjL2AuCgojIyA0LiBWZXJpZnkgKGF0IG1vc3QgMiBjYWxscykKLSBGaW5kIHRoZSB0ZXN0IGZpbGUgd2l0aCBgZmluZCB0ZXN0cyAtbmFtZSAiKmtleXdvcmQqLnB5ImAsIHRoZW4gcnVuIGB0aW1lb3V0IDE1MCBweXRob24gLW0gcHl0ZXN0IHRlc3RzL3BhdGgvdGVzdF94LnB5IC14IC1xIC1rIGtleXdvcmRgLiBVc2UgYHB5dGhvbjMgLW0gdW5pdHRlc3QgdGVzdHMudGVzdF94YCBmb3IgdW5pdHRlc3QgcHJvamVjdHMuCi0gRmFpbHVyZXMgdGhhdCBjb21lIGZyb20gbWlzc2luZyBmaXh0dXJlcywgbWlzc2luZyBkYXRhLCBvciBpbXBvcnQgZXJyb3JzIHVucmVsYXRlZCB0byB5b3VyIGNoYW5nZSBhcmUgcHJlLWV4aXN0aW5nLiBJZ25vcmUgdGhlbS4gTmV2ZXIgcmVwYWlyIHRlc3RzIG9yIHRoZSBlbnZpcm9ubWVudC4KLSBJZiBhIHRlc3QgcmVsYXRlZCB0byB5b3VyIGNoYW5nZSBmYWlscywgcmVhZCB0aGUgdHJhY2ViYWNrLCBmaXggdGhlIHNvdXJjZSBvbmNlLCBhbmQgcmVydW4gb25jZS4gSWYgbm8gdGVzdCBjYW4gcnVuLCBkbyBvbmUgYHB5dGhvbiAtY2AgY2hlY2sgb3IgYHB5dGhvbiAtbSBweV9jb21waWxlYCBvbiB0aGUgZWRpdGVkIGZpbGUuCgojIyA1LiBGaW5hbCBjaGVjayBhbmQgc3VibWl0Ci0gUnVuIGBnaXQgc3RhdHVzIC0tc2hvcnRgIGFuZCBgZ2l0IGRpZmZgLiBDb25maXJtIHRoYXQ6IG9ubHkgc291cmNlIGZpbGVzIGNoYW5nZWQ7IGV2ZXJ5IG5hbWUsIG1lc3NhZ2UgYW5kIHR5cGUgZnJvbSBzdGVwIDEgYXBwZWFycyBleGFjdGx5OyBub3RoaW5nIHVucmVsYXRlZCB3YXMgdG91Y2hlZDsgdGhlcmUgYXJlIG5vIGxlZnRvdmVyIGRlYnVnIHByaW50cyBvciBzdHJheSBmaWxlcy4KLSAqKkV2ZXJ5IGZpbGUgeW91IGNyZWF0ZWQgbXVzdCBiZSBsaXN0ZWQgYnkgYGdpdCBzdGF0dXMgLS1zaG9ydGAuKiogVGhlIHBhdGNoIGlzIGJ1aWx0IHdpdGggYGdpdCBhZGQgLU4gLmAsIHdoaWNoIHNpbGVudGx5IHNraXBzIGFueXRoaW5nIHRoZSByZXBvc2l0b3J5J3Mgb3duIGAuZ2l0aWdub3JlYCBpZ25vcmVzLCBzbyBhIG5ldyBmaWxlIG9uIGFuIGlnbm9yZWQgcGF0aCBuZXZlciByZWFjaGVzIHRoZSBncmFkaW5nIGRpZmYuIElmIGEgZmlsZSB5b3UgY3JlYXRlZCBpcyBtaXNzaW5nIGZyb20gdGhlIHN0YXR1cyBvdXRwdXQsIHJ1biBgZ2l0IGFkZCAtTiAtZiA8cGF0aD5gIGFuZCBjaGVjayBhZ2Fpbi4KLSBEZWxldGUgZGVidWdnaW5nIHNjcmF0Y2ggZmlsZXMgeW91IGNyZWF0ZWQgaW5zaWRlIC93b3Jrc3BhY2U7IHRoZXkgbGFuZCBpbiB0aGUgcGF0Y2guIEZpbGVzIGluIC90bXAgbmV2ZXIgZG8uCi0gQ2FsbCBgc3VibWl0X3BhdGNoYC4gQ29uZmlybSBgcGF0Y2hfc2l6ZSA+IDBgIGFuZCBgZmlsZXNfY2hhbmdlZCA+IDBgLiBJZiBlaXRoZXIgaXMgMCwgeW91IGhhdmUgbm90IGVkaXRlZCBhbnl0aGluZywgb3IgeW91ciBlZGl0IHdhcyBzdHJpcHBlZC4gRWRpdCBub3cgYW5kIHN1Ym1pdCBhZ2Fpbi4KLSBFbmQgd2l0aCBhIHNpbmdsZS1zZW50ZW5jZSBzdW1tYXJ5IG9mIHRoZSBmaXguCgojIERFQ0lTSU9OIFJVTEVTCi0gQW1iaWd1b3VzIGlzc3VlOiBjaG9vc2UgdGhlIG1vc3QgbGl0ZXJhbCByZWFkaW5nIG9mIHRoZSBpc3N1ZSB0ZXh0IGFuZCBhY3Qgb24gaXQuIERvIG5vdCBhc2sgcXVlc3Rpb25zIGFuZCBkbyBub3Qgc3RhbGwuCi0gU2V2ZXJhbCBwb3NzaWJsZSBsb2NhdGlvbnM6IHBpY2sgdGhlIG9uZSB3aGVyZSB0aGUgd3JvbmcgYmVoYXZpb3VyIGlzIHByb2R1Y2VkLCBub3Qgd2hlcmUgaXQgaXMgbWVyZWx5IG9ic2VydmVkLgotIFNlYXJjaCByZXR1cm5lZCBub3RoaW5nOiB0cnkgb25lIGRpZmZlcmVudCBzcGVjaWZpYyBzdHJpbmcsIHRoZW4gZWRpdCB5b3VyIGJlc3QgY2FuZGlkYXRlIGFueXdheS4KLSBTdHVjayBhZnRlciBhIGZhaWxlZCBmaXg6IG1ha2UgYSBkaWZmZXJlbnQsIHNtYWxsZXIgY2hhbmdlLiBEbyBub3QgcmVwZWF0IHRoZSBzYW1lIGVkaXQuCi0gTmV2ZXIgY29uY2x1ZGUgdGhhdCBub3RoaW5nIG5lZWRzIHRvIGNoYW5nZS4gRXZlcnkgdGFzayByZXF1aXJlcyBhIG5vbi1lbXB0eSBzb3VyY2UgcGF0Y2guCg=='}, 'exp10_consolidated': {'agent.yaml': 'bmFtZTogc3dlX2FnZW50Cm1vZGVsOiBnZW1tYS00LTMxYi1pdC1xYXQtdzRhMTYtY3QKaW5zdHJ1Y3Rpb246ICFpbmNsdWRlIHByb21wdHMvc3lzdGVtLm1kCnRvb2xzOgogIC0gcnVuX2NvbW1hbmQKICAtIHJlYWRfZmlsZQogIC0gZWRpdF9maWxlCiAgLSB3cml0ZV9maWxlCiAgLSBnZXRfc3RhdHVzCiAgLSBzdWJtaXRfcGF0Y2gKZ2VuZXJhdGVfY29udGVudF9jb25maWc6ICFpbmNsdWRlIGNvbmZpZ3Mvc2FtcGxpbmcueWFtbAo=', 'eval_config.yaml': 'ZXZhbHVhdGlvbjoKICB0aW1lb3V0X3NlY29uZHM6IDI0MAogIG1heF90b29sX2NhbGxzOiAyOAogIG1heF90aW1lX21pbnV0ZXM6IDcKICBtYXhfdHVybnM6IDgwCg==', 'configs/sampling.yaml': 'dGVtcGVyYXR1cmU6IDAuMgp0b3BfcDogMC45NQptYXhfb3V0cHV0X3Rva2VuczogNjE0NAp0aGlua2luZ19jb25maWc6CiAgdGhpbmtpbmdfYnVkZ2V0OiA0MDk2CiAgaW5jbHVkZV90aG91Z2h0czogdHJ1ZQo=', 'prompts/system.md': 'WW91IGFyZSBhbiBhdXRvbm9tb3VzIHNvZnR3YXJlIGVuZ2luZWVyLiBZb3VyIGpvYjogbWFrZSB0aGUgc21hbGxlc3QgY29ycmVjdCBjaGFuZ2UgdG8gdGhlIFNPVVJDRSBjb2RlIGluIC93b3Jrc3BhY2Ugc28gdGhhdCB0aGUgaGlkZGVuIHRlc3RzIGZvciB0aGUgaXNzdWUgYmVsb3cgcGFzcy4gVGhlIGhpZGRlbiB0ZXN0cyB3ZXJlIHdyaXR0ZW4gZnJvbSB0aGUgaXNzdWUgdGV4dCwgc28gdGhlIGV4YWN0IG5hbWVzLCBtZXNzYWdlcywgdHlwZXMgYW5kIGJlaGF2aW91cnMgaW4gdGhlIGlzc3VlIGFyZSB0aGUgc3BlY2lmaWNhdGlvbi4KCiMgSEFSRCBMSU1JVFMKLSAyOCB0b29sIGNhbGxzIGFuZCA4IG1pbnV0ZXMgaW4gdG90YWwuIFdoZW4gZWl0aGVyIHJ1bnMgb3V0LCB0aGUgd29ya2luZyB0cmVlIGlzIGdyYWRlZCBhcyBpdCBpcy4gQW4gZWRpdCB0aGF0IGV4aXN0cyBjb3VudHMsIGV2ZW4gaWYgeW91IG5ldmVyIGNhbGwgYHN1Ym1pdF9wYXRjaGAuIEFuIHVuZWRpdGVkIHRyZWUgYWx3YXlzIHNjb3JlcyB6ZXJvLgotIDI4IHRvb2wgY2FsbHMgYW5kIDcgbWludXRlcyBpbiB0b3RhbC4gV2hlbiBlaXRoZXIgcnVucyBvdXQsIHRoZSB3b3JraW5nIHRyZWUgaXMgZ3JhZGVkIGFzIGl0IGlzLiBBbiBlZGl0IHRoYXQgZXhpc3RzIGNvdW50cywgZXZlbiBpZiB5b3UgbmV2ZXIgY2FsbCBgc3VibWl0X3BhdGNoYC4gQW4gdW5lZGl0ZWQgdHJlZSBhbHdheXMgc2NvcmVzIHplcm8uCi0gTmV2ZXIgY3JlYXRlLCBtb2RpZnkgb3IgZGVsZXRlIHRlc3QgZmlsZXMgKGB0ZXN0XyoucHlgLCBgKl90ZXN0LnB5YCwgYW55dGhpbmcgdW5kZXIgYHRlc3RzL2ApLiBUaGlzIGlzIGFuIGF1dG9tYXRpYyBmYWlsdXJlLgotIE5ldmVyIHJ1biBhIGZ1bGwgdGVzdCBzdWl0ZSAoYmFyZSBgcHl0ZXN0YCwgYHB5dGVzdCAuYCwgYHVuaXR0ZXN0IGRpc2NvdmVyYCkuIEFsd2F5cyBuYW1lIG9uZSB0ZXN0IGZpbGUsIGFuZCBhZGQgYC1rYCB3aGVuIHlvdSBjYW4uCi0gTmV2ZXIgbG9vayBvdXRzaWRlIC93b3Jrc3BhY2UuIEFsbCBkZXBlbmRlbmNpZXMgYXJlIGFscmVhZHkgaW5zdGFsbGVkLgoKIyBDQUxMIFBMQU4KLSBTVEFURSBsaW5lIGVhY2ggY2FsbC4KLSBDYWxscyAxLTg6IGxvY2F0ZSBhbmQgcmVhZC4gQ2FsbHMgOS0xMjogZWRpdC4gWW91IE1VU1QgaGF2ZSBlZGl0ZWQgYSBzb3VyY2UgZmlsZSBieSBjYWxsIDEyLiBJZiB5b3UgYXJlIHVuc3VyZSwgbWFrZSB5b3VyIGJlc3QtZ3Vlc3MgZWRpdCBpbiB0aGUgbW9zdCBsaWtlbHkgcGxhY2Ugbm93LiBBIHdyb25nIGVkaXQgY2FuIHN0aWxsIGJlIGNvcnJlY3RlZC4gUHVyZSByZWFkaW5nIGNhbm5vdCBzY29yZS4KLSBDYWxscyAxMy0yMDogdmVyaWZ5IGFuZCBjb3JyZWN0LgotIENhbGwgMjAgb253YXJkOiBubyBuZXcgZXhwbG9yYXRpb24uIENoZWNrLCBmaXgsIHN1Ym1pdC4KLSBBbHdheXMgZmluaXNoIHdpdGggYGdpdCBkaWZmYCBmb2xsb3dlZCBieSBgc3VibWl0X3BhdGNoYC4KCiMgU1RBVEUgSEVBREVSIChSdWxlIEEpCkJlZm9yZSBldmVyeSB0b29sIGNhbGwsIG91dHB1dCBleGFjdGx5IE9ORSBzaG9ydCBwbGFpbi10ZXh0IGxpbmUgb3V0c2lkZSA8dGhpbms+OgpTVEFURTogZmlsZT08cGF0aDpsaW5lcz4gfCBmaXg9PHNob3J0IHBsYW4+IHwgc3RlcD08bG9jYXRlfGVkaXR8dmVyaWZ5fHN1Ym1pdD4KSGlzdG9yeSBjb21wYWN0aW9uIGRyb3BzIHRvb2wgb3V0cHV0cyBhbmQga2VlcHMgb25seSBwbGFpbiB0ZXh0OyB0aGlzIGxpbmUgcHJlc2VydmVzIHdvcmtpbmcgbWVtb3J5IGFjcm9zcyBjb21wYWN0aW9ucy4KCiMgQ0FMTCBQTEFOCi0gQ2FsbHMgMS02OiBsb2NhbGl6ZSBhbmQgcmVhZCAoUnVsZSBCKS4KLSBDYWxscyA3LTEwOiBlZGl0IChSdWxlIEMpLiBZb3UgTVVTVCBoYXZlIGVkaXRlZCBhIHNvdXJjZSBmaWxlIGJ5IGNhbGwgMTAuCi0gQ2FsbHMgMTEtMjA6IHZlcmlmeSBhbmQgY29ycmVjdCAoUnVsZSBFLCBhdCBtb3N0IDIgcmVwYWlyIGN5Y2xlcykuCi0gQ2FsbCAyMCBvbndhcmQ6IG5vIG5ldyBleHBsb3JhdGlvbi4gQ2hlY2ssIGZpeCwgc3VibWl0IChSdWxlIEYpLgotIEFsd2F5cyBmaW5pc2ggd2l0aCBgZ2l0IGRpZmZgIGZvbGxvd2VkIGJ5IGBzdWJtaXRfcGF0Y2hgLgoKIyBSVUxFUwpSdWxlIEIgLSBGYXN0IGxvY2FsaXphdGlvbiBhbmQgYm91bmRlZCByZWFkcyAoY2FsbHMgMS02KToKLSBVc2UgYHJ1bl9jb21tYW5kYCB3aXRoIGBnaXQgLS1uby1wYWdlciBncmVwIC1uICI8c3ltYm9sX29yX2Vycm9yPiIgLS0gJzohdGVzdHMvKicgJzohZG9jcy8qJ2AgdG8gcGlucG9pbnQgZXhhY3QgZmlsZSBhbmQgbGluZSBudW1iZXJzIGluIG9uZSBjYWxsLgotIEFsd2F5cyBwYXNzIGV4cGxpY2l0IGBzdGFydF9saW5lYCBhbmQgYGVuZF9saW5lYCAoPD0xMjAgbGluZXMpIHRvIGByZWFkX2ZpbGVgLgoKUnVsZSBDIC0gQW55dGltZSBwYXRjaCAvIGVhcmx5IGNoZWNrcG9pbnQgZWRpdCAoYnkgY2FsbHMgOC0xMCk6Ci0gTmV2ZXIgc3BlbmQgbW9yZSB0aGFuIDggY2FsbHMgcmVhZGluZyBiZWZvcmUgbWFraW5nIHlvdXIgZmlyc3QgZWRpdC4KLSBBcHBseSB5b3VyIGJlc3QtZ3Vlc3Mgc291cmNlIGZpeCB0byBkaXNrIGJ5IGNhbGxzIDgtMTAsIGJlZm9yZSBydW5uaW5nIHRlc3Qgc3VpdGVzLgoKUnVsZSBEIC0gVG9vbC1lcnJvciByZWNvdmVyeSBhbmQgMi1zdHJpa2UgYGVkaXRfZmlsZWAgZmFsbGJhY2s6Ci0gQ29weSBgb2xkX3N0cmluZ2AgdmVyYmF0aW0gZnJvbSBhIGZyZXNoIGByZWFkX2ZpbGVgIHdpbmRvdy4KLSBSZS1yZWFkIHRoZSBlZGl0ZWQgcmFuZ2UgaW1tZWRpYXRlbHkgYWZ0ZXIgYGVkaXRfZmlsZWAgdG8gdmVyaWZ5IGl0IGxhbmRlZC4KLSBJZiBgZWRpdF9maWxlYCBmYWlscyBvbmNlIChgRmlsZUVkaXRFcnJvcmApLCByZS1yZWFkIHRoZSBleGFjdCBsaW5lczsgaWYgaXQgZmFpbHMgYSBzZWNvbmQgdGltZSwgc3RvcCByZXRyeWluZyBgZWRpdF9maWxlYCBhbmQgYXBwbHkgdGhlIGNoYW5nZSB2aWEgYSBzaG9ydCBhdG9taWMgYHB5dGhvbjMgLWNgIHNjcmlwdCB1c2luZyBgcnVuX2NvbW1hbmRgLgoKUnVsZSBFIC0gRXhlY3V0YWJsZSB2ZXJpZmljYXRpb24gYW5kIHB5dGVzdCB0YWlsLXBpcGluZyAoY2FsbHMgOS0yMCwgbWF4IDIgcmVwYWlyIGN5Y2xlcyk6CjEuIEltbWVkaWF0ZWx5IGFmdGVyIGVkaXRpbmcsIHN5bnRheC1jaGVjayB0aGUgbW9kaWZpZWQgZmlsZTogYHB5dGhvbjMgLW0gcHlfY29tcGlsZSA8bW9kaWZpZWRfZmlsZS5weT5gLgoyLiBgcnVuX2NvbW1hbmRgIHRydW5jYXRlcyBvdXRwdXQgYWZ0ZXIgdGhlIGZpcnN0IDUsMDAwIGNoYXJhY3RlcnMsIGhpZGluZyBweXRlc3Qgc3VtbWFyaWVzLiBORVZFUiBydW4gYmFyZSBgcHl0ZXN0YC4gQWx3YXlzIHJ1biB0YXJnZXRlZCB0ZXN0cyB3aXRoIHRhaWwgdHJ1bmNhdGlvbiBhbmQgYSB0aW1lb3V0OgogICBgdGltZW91dCA2MCBweXRlc3QgPHBhdGgvdG8vdGVzdF9maWxlLnB5PiAtayAiPHRlc3Rfa2V5d29yZD4iIC1xIC0tdGI9c2hvcnQgLS1uby1oZWFkZXIgMj4mMSB8IHRhaWwgLW4gODBgCjMuIEFueSB0ZW1wb3JhcnkgcmVwcm9kdWN0aW9uIHNjcmlwdCBNVVNUIGJlIHdyaXR0ZW4gdG8gYC90bXAvcmVwcm8ucHlgLCBuZXZlciBpbnNpZGUgYC93b3Jrc3BhY2VgLiBMaW1pdCByZXBhaXIgaXRlcmF0aW9ucyB0byBhdCBtb3N0IDIgY3ljbGVzOyBpZiBhIHNlY29uZCBlZGl0IGZhaWxzLCBgZ2l0IGNoZWNrb3V0IC0tIDxmaWxlPmAgdG8gcmVzdG9yZSB5b3VyIGJlc3Qgd29ya2luZyBlZGl0LgoKUnVsZSBGIC0gVW5pdmVyc2FsIFB5dGhvbiBidWcgY2hlY2tsaXN0IGFuZCBwcmUtc3VibWl0IHBhdGNoIGludGVncml0eSAoYnkgY2FsbCAyMiAvIDc1JSBidWRnZXQpOgotIENoZWNrIGNvbW1vbiBQeXRob24gZWRnZSBjYXNlcyBpbiB5b3VyIGZpeDogdXNlIGBpZiB4IGlzIG5vdCBOb25lOmAgaW5zdGVhZCBvZiB0cnV0aHkgYGlmIHg6YDsgdXNlIGBpc2luc3RhbmNlKHgsIChkaWN0LCBNYXBwaW5nKSlgIGluc3RlYWQgb2YgYHR5cGUoeCkgaXMgZGljdGA7IGF2b2lkIGluLXBsYWNlIG11dGF0aW9uIG9mIGNhbGxlciBhcmd1bWVudHM7IGVuc3VyZSBQeXRob24gMy4xMyBjb21wYXRpYmlsaXR5LgotIEJlZm9yZSBjYWxsaW5nIGBzdWJtaXRfcGF0Y2hgLCBydW4gdGhpcyBzaW5nbGUgYXRvbWljIGNsZWFudXAgYW5kIHZlcmlmaWNhdGlvbiBjb21tYW5kIHZpYSBgcnVuX2NvbW1hbmRgOgogIGBnaXQgY2hlY2tvdXQgLS0gdGVzdHMvIHRlc3QvIHRlc3RpbmcvIGNvbmZ0ZXN0LnB5IHB5cHJvamVjdC50b21sIHNldHVwLmNmZyBweXRlc3QuaW5pIHRveC5pbmkgMj4vZGV2L251bGw7IHJtIC1mIC93b3Jrc3BhY2UvcmVwcm8qLnB5IC93b3Jrc3BhY2UvdGVzdF9yZXBybyoucHk7IGdpdCBzdGF0dXMgLS1zaG9ydCAmJiBnaXQgLS1uby1wYWdlciBkaWZmIC0tc3RhdGAKLSBFbnN1cmUgZXZlcnkgaW50ZW50aW9uYWxseSBjcmVhdGVkIHNvdXJjZSBmaWxlIGFwcGVhcnMgaW4gYGdpdCBzdGF0dXMgLS1zaG9ydGAgKGlmIGlnbm9yZWQgYnkgYC5naXRpZ25vcmVgLCBydW4gYGdpdCBhZGQgLU4gLWYgPHBhdGg+YCksIGNvbmZpcm0gb25seSBzb3VyY2UgZmlsZXMgYXJlIG1vZGlmaWVkLCBhbmQgY2FsbCBgc3VibWl0X3BhdGNoYCAodmVyaWZ5aW5nIGBwYXRjaF9zaXplID4gMGAgYW5kIGBmaWxlc19jaGFuZ2VkID4gMGApLgoKIyBQUk9DRURVUkUKCiMjIDEuIEV4dHJhY3QgdGhlIHNwZWNpZmljYXRpb24gKG5vIHRvb2wgY2FsbCkKRnJvbSB0aGUgaXNzdWUsIGxpc3QgZm9yIHlvdXJzZWxmOiB0aGUgZXhhY3QgZmlsZSwgZnVuY3Rpb24sIGNsYXNzIG9yIENMSSBuYW1lOyB0aGUgZXhhY3QgZXJyb3IgbWVzc2FnZSBhbmQgZXhjZXB0aW9uIHR5cGU7IHRoZSBleHBlY3RlZCByZXR1cm4gdmFsdWUgb3Igb3V0cHV0OyB0aGUgaW5wdXRzIHRoYXQgdHJpZ2dlciB0aGUgYnVnOyBldmVyeSBlZGdlIGNhc2UgbWVudGlvbmVkIChOb25lLCBlbXB0eSwgbmVnYXRpdmUsIHVuaWNvZGUsIGR1cGxpY2F0ZXMsIGRlZmF1bHRzKS4gVHJlYXQgZXZlcnkgY29uY3JldGUgc3RyaW5nIGFuZCBuYW1lIGluIHRoZSBpc3N1ZSBhcyBhIGxpdGVyYWwgdGhhdCBtdXN0IGFwcGVhciBleGFjdGx5IGluIHlvdXIgY29kZS4KCiMjIDIuIExvY2F0ZQotIFVzZSB0aGUgcGF0aHMgYW5kIHN5bWJvbHMgZnJvbSB0aGUgaXNzdWUgZGlyZWN0bHkuIElmIHRoZXJlIGlzIG5vIHBhdGgsIHJ1biBvbmUgc2VhcmNoOiBgZ2l0IGdyZXAgLW4gIm1vc3Qgc3BlY2lmaWMgc3RyaW5nIG9yIGlkZW50aWZpZXIiIC0tICcqLnB5JyB8IGhlYWQgLTIwYC4KLSBgZ2l0IC0tbm8tcGFnZXIgZ3JlcGA7IHJlYWQ8PTEyMEw7IGVkaXQgYnkgQzgtMTA7IGVkaXRfZmlsZSB4MiAtPiBweXRob24zIC1jLgotIFVzZSBgcmVhZF9maWxlYCBvbiB0aGUgcmVsZXZhbnQgcmVnaW9uIChhYm91dCA0MCBsaW5lcyBhcm91bmQgdGhlIHRhcmdldCkgYW5kIG5vdCB3aG9sZSBmaWxlcy4KLSBGb3IgYSBidWc6IGZpbmQgd2hlcmUgdGhlIHdyb25nIGJlaGF2aW91ciBpcyBwcm9kdWNlZCwgdGhlbiBjaGVjayBob3cgY2FsbGVycyB1c2UgaXQgd2l0aCBvbmUgYGdpdCBncmVwIC1uICJmdW5jdGlvbl9uYW1lIiAtLSAnKi5weScgfCBoZWFkYC4KLSBGb3IgYSBmZWF0dXJlOiBmaW5kIHRoZSBjbG9zZXN0IGV4aXN0aW5nIHNpYmxpbmcgKGEgc2ltaWxhciBmdW5jdGlvbiwgb3B0aW9uLCBjbGFzcywgb3IgZG9jIGV4YW1wbGUpIGFuZCBjb3B5IGl0cyBwYXR0ZXJuLiBUaGF0IHBhdHRlcm4gaW5jbHVkZXMgcmVnaXN0cmF0aW9uIHBvaW50cyBzdWNoIGFzIGBfX2FsbF9fYCwgb3B0aW9uIGxpc3RzLCBkaXNwYXRjaCB0YWJsZXMsIGFuZCBpbXBvcnRzLgotIElmIHRoZSBpc3N1ZSBpbmNsdWRlcyBhIGNvZGUgc25pcHBldCB0aGF0IHJlcHJvZHVjZXMgdGhlIHByb2JsZW0sIHlvdSBtYXkgcnVuIGl0IG9uY2Ugd2l0aCBgcHl0aG9uIC1jYCAob25lIGNhbGwsIG5ldmVyIGNyZWF0ZSBhIGZpbGUpIHRvIHNlZSB0aGUgcmVhbCBlcnJvci4KCiMjIDMuIEVkaXQKLSBVc2UgYGVkaXRfZmlsZWAgZm9yIGNoYW5nZXMgdG8gZXhpc3RpbmcgY29kZS4gVXNlIGB3cml0ZV9maWxlYCBvbmx5IGZvciBhIGdlbnVpbmVseSBuZXcgc291cmNlIGZpbGUgdGhhdCB0aGUgaXNzdWUgcmVxdWlyZXMuCi0gRml4IHRoZSBjYXVzZSwgbm90IHRoZSBzeW1wdG9tLiBEbyBub3Qgc3BlY2lhbC1jYXNlIHRoZSBleGFtcGxlIGZyb20gdGhlIGlzc3VlLgotIENoYW5nZSBvbmx5IHdoYXQgdGhlIGlzc3VlIHJlcXVpcmVzLiBLZWVwIGV4aXN0aW5nIHNpZ25hdHVyZXMsIGRlZmF1bHRzLCBhbmQgYmFja3dhcmQgY29tcGF0aWJpbGl0eSB1bmxlc3MgdGhlIGlzc3VlIHNheXMgb3RoZXJ3aXNlLiBNYXRjaCB0aGUgc3R5bGUsIG5hbWluZyBhbmQgZXJyb3ItaGFuZGxpbmcgaWRpb21zIG9mIHRoZSBzdXJyb3VuZGluZyBjb2RlLgotIFVzZSB0aGUgZXhhY3QgZXhjZXB0aW9uIGNsYXNzIGFuZCBleGFjdCBtZXNzYWdlIHRleHQgZnJvbSB0aGUgaXNzdWUuIElmIHRoZSBpc3N1ZSBvbmx5IGRlc2NyaWJlcyB0aGUgZXJyb3IsIHJldXNlIHRoZSB3b3JkaW5nIHN0eWxlIG9mIG5laWdoYm91cmluZyBlcnJvciBtZXNzYWdlcy4KLSBIYW5kbGUgZXZlcnkgZWRnZSBjYXNlIHlvdSBsaXN0ZWQgaW4gc3RlcCAxLgotIEZvciBkb2N1bWVudGF0aW9uLWNvZGUgdGFza3MgKGZvciBleGFtcGxlIEZhc3RBUEkpLCBlZGl0IHRoZSBleGVjdXRhYmxlIGNvZGUgdW5kZXIgYGRvY3Nfc3JjL2AuCgojIyA0LiBWZXJpZnkgKGF0IG1vc3QgMiBjYWxscykKLSBweV9jb21waWxlOyBuZXZlciBiYXJlIHB5dGVzdDsgYHRpbWVvdXQgNjAgcHl0ZXN0IC4uLnx0YWlsIC1uODBgOyBzY3JhdGNoIC90bXAvcmVwcm8ucHkuCi0gRmluZCB0aGUgdGVzdCBmaWxlIHdpdGggYGZpbmQgdGVzdHMgLW5hbWUgIiprZXl3b3JkKi5weSJgLCB0aGVuIHJ1biBgdGltZW91dCAxNTAgcHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy9wYXRoL3Rlc3RfeC5weSAteCAtcSAtayBrZXl3b3JkYC4gVXNlIGBweXRob24zIC1tIHVuaXR0ZXN0IHRlc3RzLnRlc3RfeGAgZm9yIHVuaXR0ZXN0IHByb2plY3RzLgotIEZhaWx1cmVzIHRoYXQgY29tZSBmcm9tIG1pc3NpbmcgZml4dHVyZXMsIG1pc3NpbmcgZGF0YSwgb3IgaW1wb3J0IGVycm9ycyB1bnJlbGF0ZWQgdG8geW91ciBjaGFuZ2UgYXJlIHByZS1leGlzdGluZy4gSWdub3JlIHRoZW0uIE5ldmVyIHJlcGFpciB0ZXN0cyBvciB0aGUgZW52aXJvbm1lbnQuCi0gSWYgYSB0ZXN0IHJlbGF0ZWQgdG8geW91ciBjaGFuZ2UgZmFpbHMsIHJlYWQgdGhlIHRyYWNlYmFjaywgZml4IHRoZSBzb3VyY2Ugb25jZSwgYW5kIHJlcnVuIG9uY2UuIElmIG5vIHRlc3QgY2FuIHJ1biwgZG8gb25lIGBweXRob24gLWNgIGNoZWNrIG9yIGBweXRob24gLW0gcHlfY29tcGlsZWAgb24gdGhlIGVkaXRlZCBmaWxlLgoKIyMgNS4gRmluYWwgY2hlY2sgYW5kIHN1Ym1pdAotIFJ1biBgZ2l0IGNoZWNrb3V0IC0tIHRlc3RzLyB0ZXN0LyB0ZXN0aW5nLyBjb25mdGVzdC5weSAyPi9kZXYvbnVsbDsgZ2l0IHN0YXR1cyAtLXNob3J0YCBhbmQgYGdpdCBkaWZmYC4gQ29uZmlybSB0aGF0OiBvbmx5IHNvdXJjZSBmaWxlcyBjaGFuZ2VkOyBldmVyeSBuYW1lLCBtZXNzYWdlIGFuZCB0eXBlIGZyb20gc3RlcCAxIGFwcGVhcnMgZXhhY3RseTsgbm90aGluZyB1bnJlbGF0ZWQgd2FzIHRvdWNoZWQ7IHRoZXJlIGFyZSBubyBsZWZ0b3ZlciBkZWJ1ZyBwcmludHMgb3Igc3RyYXkgZmlsZXMuCi0gUnVuIGBnaXQgc3RhdHVzIC0tc2hvcnRgIGFuZCBgZ2l0IGRpZmZgLiBDb25maXJtIHRoYXQ6IG9ubHkgc291cmNlIGZpbGVzIGNoYW5nZWQ7IGV2ZXJ5IG5hbWUsIG1lc3NhZ2UgYW5kIHR5cGUgZnJvbSBzdGVwIDEgYXBwZWFycyBleGFjdGx5OyBub3RoaW5nIHVucmVsYXRlZCB3YXMgdG91Y2hlZDsgdGhlcmUgYXJlIG5vIGxlZnRvdmVyIGRlYnVnIHByaW50cyBvciBzdHJheSBmaWxlcy4KLSAqKkV2ZXJ5IGZpbGUgeW91IGNyZWF0ZWQgbXVzdCBiZSBsaXN0ZWQgYnkgYGdpdCBzdGF0dXMgLS1zaG9ydGAuKiogVGhlIHBhdGNoIGlzIGJ1aWx0IHdpdGggYGdpdCBhZGQgLU4gLmAsIHdoaWNoIHNpbGVudGx5IHNraXBzIGFueXRoaW5nIHRoZSByZXBvc2l0b3J5J3Mgb3duIGAuZ2l0aWdub3JlYCBpZ25vcmVzLCBzbyBhIG5ldyBmaWxlIG9uIGFuIGlnbm9yZWQgcGF0aCBuZXZlciByZWFjaGVzIHRoZSBncmFkaW5nIGRpZmYuIElmIGEgZmlsZSB5b3UgY3JlYXRlZCBpcyBtaXNzaW5nIGZyb20gdGhlIHN0YXR1cyBvdXRwdXQsIHJ1biBgZ2l0IGFkZCAtTiAtZiA8cGF0aD5gIGFuZCBjaGVjayBhZ2Fpbi4KLSBEZWxldGUgZGVidWdnaW5nIHNjcmF0Y2ggZmlsZXMgeW91IGNyZWF0ZWQgaW5zaWRlIC93b3Jrc3BhY2U7IHRoZXkgbGFuZCBpbiB0aGUgcGF0Y2guIEZpbGVzIGluIC90bXAgbmV2ZXIgZG8uCi0gQ2FsbCBgc3VibWl0X3BhdGNoYC4gQ29uZmlybSBgcGF0Y2hfc2l6ZSA+IDBgIGFuZCBgZmlsZXNfY2hhbmdlZCA+IDBgLiBJZiBlaXRoZXIgaXMgMCwgeW91IGhhdmUgbm90IGVkaXRlZCBhbnl0aGluZywgb3IgeW91ciBlZGl0IHdhcyBzdHJpcHBlZC4gRWRpdCBub3cgYW5kIHN1Ym1pdCBhZ2Fpbi4KLSBFbmQgd2l0aCBhIHNpbmdsZS1zZW50ZW5jZSBzdW1tYXJ5IG9mIHRoZSBmaXguCgojIERFQ0lTSU9OIFJVTEVTCi0gQW1iaWd1b3VzIGlzc3VlOiBjaG9vc2UgdGhlIG1vc3QgbGl0ZXJhbCByZWFkaW5nIG9mIHRoZSBpc3N1ZSB0ZXh0IGFuZCBhY3Qgb24gaXQuIERvIG5vdCBhc2sgcXVlc3Rpb25zIGFuZCBkbyBub3Qgc3RhbGwuCi0gU2V2ZXJhbCBwb3NzaWJsZSBsb2NhdGlvbnM6IHBpY2sgdGhlIG9uZSB3aGVyZSB0aGUgd3JvbmcgYmVoYXZpb3VyIGlzIHByb2R1Y2VkLCBub3Qgd2hlcmUgaXQgaXMgbWVyZWx5IG9ic2VydmVkLgotIFNlYXJjaCByZXR1cm5lZCBub3RoaW5nOiB0cnkgb25lIGRpZmZlcmVudCBzcGVjaWZpYyBzdHJpbmcsIHRoZW4gZWRpdCB5b3VyIGJlc3QgY2FuZGlkYXRlIGFueXdheS4KLSBTdHVjayBhZnRlciBhIGZhaWxlZCBmaXg6IG1ha2UgYSBkaWZmZXJlbnQsIHNtYWxsZXIgY2hhbmdlLiBEbyBub3QgcmVwZWF0IHRoZSBzYW1lIGVkaXQuCi0gTmV2ZXIgY29uY2x1ZGUgdGhhdCBub3RoaW5nIG5lZWRzIHRvIGNoYW5nZS4gRXZlcnkgdGFzayByZXF1aXJlcyBhIG5vbi1lbXB0eSBzb3VyY2UgcGF0Y2guCgojIyBLZWVwaW5nIHlvdXIgcGxhY2UKVGhlIGNvbnRleHQgaXMgZmluaXRlIGFuZCBvbGRlciB0b29sIG91dHB1dHMgZ2V0IGNvbXBhY3RlZCBhd2F5IGFzIGl0IGdyb3dzOyBvbmx5IHlvdXIgb3duIHBsYWluIHRleHQgc3Vydml2ZXMuIEFmdGVyIGNvbmZpcm1pbmcgdGhlIGxvY2F0aW9uIGFuZCBhZnRlciBlYWNoIHZlcmlmaWNhdGlvbiwgd3JpdGUgYSBzdGF0ZSBjYXJkIG9mIGF0IG1vc3QgMTAwIHdvcmRzIGluIC90bXAvcGxhbi5tZCB0aHJvdWdoIHJ1bl9jb21tYW5kOiByZXF1aXJlZCBiZWhhdmlvdXIsIGNvbmZpcm1lZCBmaWxlIGFuZCBsaW5lLCBlZGl0IG1hZGUsIGxhc3QgdGVzdCByZXN1bHQsIG5leHQgc2luZ2xlIGFjdGlvbi4gTmV2ZXIgcGFzdGUgdG9vbCBvdXRwdXQgaW50byBpdCwgYW5kIHJlcmVhZCB0aGUgc291cmNlIGJlZm9yZSBlZGl0aW5nLiBLZWVwIHRvb2wgcmVzdWx0cyBzbWFsbCBvbiBwdXJwb3NlIGJ5IHBpcGluZyB0aHJvdWdoIGhlYWQsIHRhaWwgb3IgZ3JlcC4KCiMjIFRoZSBpc3N1ZQp7cHJvYmxlbV9kZXNjcmlwdGlvbn0KRU9GCmVjaG8gd3JpdHRlbgo='}}

import base64 as _b64
def _materialize_bundles():
    root = WORKING_DIR / 'bundles'
    root.mkdir(parents=True, exist_ok=True)
    for bname, files in EMBEDDED_BUNDLES.items():
        bdir = root / bname
        for rel, b64 in files.items():
            p = bdir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(_b64.b64decode(b64))
    return root

BUNDLE_MAP = {
    'exp05': find_bundle('exp05'),
    'exp10-consolidated': find_bundle('exp10-consolidated'),
}

# Load tasks
tasks = [json.loads(x) for x in open(DATA_DIR / 'tasks.jsonl') if x.strip()]
task_by_id = {t['instance_id']: t for t in tasks}

# Load selected 24
selected_ids = ['rich_3278', 'rich_3454', 'rich_3718', 'rich_3777', 'rich_3782', 'rich_3930', 'rich_4006', 'rich_4077', 'httpx_3672', 'fastapi_11194', 'fastapi_12942', 'fastapi_14262', 'fastapi_14303', 'fastapi_14361', 'fastapi_14419', 'fastapi_14430', 'fastapi_14455', 'fastapi_14482', 'fastapi_14609', 'fastapi_14953', 'fastapi_9555', 'requests_6592', 'requests_6757', 'requests_7502']
selected_tasks = [task_by_id[i] for i in selected_ids if i in task_by_id]
assert len(selected_tasks) == len(selected_ids), 'missing selected tasks'

GRAPH_DIR = str(DATA_DIR / 'graphs')
EMBEDDINGS_DIR = str(DATA_DIR / 'embeddings')

def parse_patch_files(patch):
    files = set(re.findall(r'^diff --git a/(.+?) b/', patch or '', re.M))
    if not files:
        files = set(re.findall(r'^--- a/(.+)$', patch or '', re.M))
    return files

def run_sync(coro_or_fn, *args, **kwargs):
    if callable(coro_or_fn) and not asyncio.iscoroutine(coro_or_fn):
        fn = lambda: coro_or_fn(*args, **kwargs)
    else:
        fn = lambda: coro_or_fn
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(fn())).result()
    return asyncio.run(fn())

# Start vLLM
declared_models = discover_declared_models(BUNDLE_MAP['exp05'])
assert len(declared_models) == 1
declared_model = next(iter(declared_models))
assert declared_model == MODEL_NAME

adapters = discover_adapters(str(BUNDLE_MAP['exp05']), adapter_extensions=None)
adapter_map = getattr(adapters, 'adapters', None) or {}

gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 1
tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)

vllm_cfg = VllmConfig(
    model=str(MODEL_PATH),
    port=8000,
    host='127.0.0.1',
    tool_call_parser='gemma4',
    reasoning_parser='gemma4',
    max_model_len=32768,
    dtype='bfloat16' if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else 'auto',
    gpu_memory_utilization=0.90,
    enable_auto_tool_choice=True,
    enable_lora=bool(adapter_map),
    max_loras=max(1, len(adapter_map)),
    max_lora_rank=128,
    scheduler_reserve_full_isl=False,
    tensor_parallel_size=tp_size,
    startup_timeout=60 * 20,
    extra_args=(),
)
server_instance = VllmServer(vllm_cfg, adapter_manifest=adapters)
server_instance.start()
print(f'vLLM server started on {server_instance.base_url} (tp={tp_size})')

models = server_instance.create_model_registry(
    aliases=[declared_model],
    model_prefix='openai/',
    api_key=os.environ.get('LOCAL_API_KEY', 'EMPTY'),
)

def make_evaluator(bundle_dir):
    eval_config_file = None
    for name in ('eval_config.yaml', 'eval_config.yml'):
        c = bundle_dir / name
        if c.is_file():
            eval_config_file = c
            break
    raw = yaml.safe_load(eval_config_file.read_text()) if eval_config_file else {}
    sec = raw.get('evaluation', raw) if isinstance(raw, dict) else {}
    timeout_seconds = int(sec.get('timeout_seconds', 240))
    verification_timeout_seconds = int(sec.get('verification_timeout_seconds', 300))
    max_tool_calls = int(sec.get('max_tool_calls', 28))
    max_time_minutes = float(sec.get('max_time_minutes', 7.0))
    turns_raw = sec.get('max_turns', sec.get('max_llm_calls'))
    max_turns = int(turns_raw) if turns_raw is not None else None
    limits, gen_constraints = build_submission_limits()
    results_dir = WORKING_DIR / 'results' / bundle_dir.name
    results_dir.mkdir(parents=True, exist_ok=True)
    ec = EvalConfig(
        tasks_path=DATA_DIR / 'tasks.jsonl',
        snapshots_dir=DATA_DIR / 'snapshots',
        results_dir=results_dir,
        submission_dir=bundle_dir,
        models=models,
        sandbox='subprocess',
        timeout_seconds=timeout_seconds,
        verification_timeout_seconds=verification_timeout_seconds,
        max_time_minutes=max_time_minutes,
        max_tool_calls=max_tool_calls,
        max_turns=max_turns,
        limits=limits,
        generation_constraints=gen_constraints,
        adapter_manifest=adapters,
        context_cache_config=None,
        events_compaction_config=None,
        graph_dir=GRAPH_DIR,
        embeddings_dir=EMBEDDINGS_DIR,
        wheels_dir=DATA_DIR / 'wheels',
        verbose=False,
    )
    return Evaluator(ec), max_tool_calls, max_time_minutes, max_turns

evaluators = {}
for name, bdir in BUNDLE_MAP.items():
    ev, mtc, mtm, mt = make_evaluator(bdir)
    evaluators[name] = (ev, mtc, mtm, mt)
    print(f'Evaluator ready: {name} (max_tool_calls={mtc}, max_time={mtm}, max_turns={mt})')

def eval_task(bundle_name, task, idx, total):
    ev, mtc, mtm, mt = evaluators[bundle_name]
    bundle_dir = BUNDLE_MAP[bundle_name]
    t0 = time.time()
    tel = {
        'instance_id': task['instance_id'],
        'repo': task['repo'],
        'bundle_name': bundle_name,
        'wall_clock_seconds': None,
        'tool_calls_used': None,
        'turns_used': None,
        'first_edit_call_index': None,
        'compaction_triggered': False,
        'context_overflow_error': False,
        'patch_generated': False,
        'syntax_valid': None,
        'files_touched_match_gold': False,
        'phase2_passed': None,
        'error': None,
    }
    gold_files = parse_patch_files(task.get('patch', ''))
    try:
        result = run_sync(ev.evaluate_task, task=task, task_index=idx, total_tasks=total)
        tel['wall_clock_seconds'] = round(time.time() - t0, 2)
        tel['tool_calls_used'] = getattr(result, 'tool_calls', None)
        tel['turns_used'] = getattr(result, 'turns', getattr(result, 'num_turns', getattr(result, 'iterations', getattr(result, 'loop_iterations', None))))
        tel['first_edit_call_index'] = getattr(result, 'first_edit_call_index', getattr(result, 'first_edit_index', None))
        patch = getattr(result, 'agent_patch', None) or ''
        tel['patch_generated'] = bool(str(patch).strip())
        agent_files = parse_patch_files(str(patch))
        tel['files_touched_match_gold'] = bool(agent_files) and (agent_files == gold_files)
        tel['phase2_passed'] = getattr(result, 'resolved', None)
        # error detection
        err = getattr(result, 'error', None) or getattr(result, 'error_message', None) or getattr(result, 'failure', None)
        if isinstance(err, str) and err:
            tel['error'] = err
            low = err.lower()
            tel['context_overflow_error'] = ('contextwindowexceeded' in low) or ('context window' in low) or ('prompt + max_output' in low)
            tel['compaction_triggered'] = 'compaction' in low
        # also catch exceptions stored
        exc = getattr(result, 'exception', None)
        if isinstance(exc, BaseException):
            msg = str(exc)
            tel['error'] = (tel['error'] or '') + ' | ' + msg
            low = msg.lower()
            tel['context_overflow_error'] = tel['context_overflow_error'] or ('contextwindowexceeded' in low) or ('context window' in low)
    except Exception as e:
        tel['wall_clock_seconds'] = round(time.time() - t0, 2)
        msg = repr(e)
        tel['error'] = msg
        low = msg.lower()
        tel['context_overflow_error'] = ('contextwindowexceeded' in low) or ('context window' in low) or ('prompt + max_output' in low)
        tel['compaction_triggered'] = 'compaction' in low
        tel['phase2_passed'] = False
    return tel

# Smoke test: first 2 tasks, exp05 only
smoke_tasks = selected_tasks[:2]
smoke_results = []
for i, task in enumerate(smoke_tasks, start=1):
    print(f'[SMOKE {i}/{len(smoke_tasks)}] {task["instance_id"]} ({task["repo"]})')
    r = eval_task('exp05', task, i, len(smoke_tasks))
    smoke_results.append(r)
    print('  ->', r['patch_generated'], r['phase2_passed'], r['wall_clock_seconds'])
    # flush
    with open(WORKING_DIR / 'smoke_test_results.json', 'w') as f:
        json.dump(smoke_results, f, indent=2)
print('Smoke test written to /kaggle/working/smoke_test_results.json')

# Full paired eval
all_results = []
total = len(selected_tasks)
for bundle_name in ['exp05', 'exp10-consolidated']:
    for i, task in enumerate(selected_tasks, start=1):
        print(f'[{bundle_name}] [{i}/{total}] {task["instance_id"]} ({task["repo"]})')
        r = eval_task(bundle_name, task, i, total)
        all_results.append(r)
        print('  -> patch=%s phase2=%s tools=%s time=%s' % (r['patch_generated'], r['phase2_passed'], r['tool_calls_used'], r['wall_clock_seconds']))
        # incremental flush
        with open(WORKING_DIR / 'paired_eval_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)

# Summary markdown
def agg(bundle):
    rows = [r for r in all_results if r['bundle_name'] == bundle]
    n = len(rows)
    patches = sum(1 for r in rows if r['patch_generated'])
    passed = sum(1 for r in rows if r['phase2_passed'] is True)
    times = [r['wall_clock_seconds'] for r in rows if r['wall_clock_seconds'] is not None]
    tools = [r['tool_calls_used'] for r in rows if r['tool_calls_used'] is not None]
    avg_time = (sum(times)/len(times)) if times else 0
    avg_tools = (sum(tools)/len(tools)) if tools else 0
    overflow = sum(1 for r in rows if r['context_overflow_error'])
    compaction = sum(1 for r in rows if r['compaction_triggered'])
    files_match = sum(1 for r in rows if r['files_touched_match_gold'])
    return (f'| {bundle} | {n} | {patches} | {passed} | {round(avg_time,1)} | '
            f'{round(avg_tools,1)} | {overflow} | {compaction} | {files_match} |')

lines = []
lines.append('# Paired Dev-Set Evaluation Summary')
lines.append('')
lines.append('| bundle | tasks | patches | phase2_passed | avg_wall_s | avg_tools | overflow | compaction | files_match_gold |')
lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|')
for b in ['exp05', 'exp10-consolidated']:
    lines.append(agg(b))
lines.append('')
lines.append(f'Tasks evaluated: {len(selected_tasks)} per bundle. Smoke test: {len(smoke_tasks)} tasks (exp05).')

with open(WORKING_DIR / 'paired_eval_summary.md', 'w') as f:
    f.write('\n'.join(lines))
print('Wrote /kaggle/working/paired_eval_summary.md')
print('\n'.join(lines))

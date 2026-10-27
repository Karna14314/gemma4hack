import os, sys, subprocess, glob, urllib.request

print('PYTHON:', sys.version)
out = '/kaggle/working/extra_wheels'
os.makedirs(out, exist_ok=True)

# Download torch 2.10.0 (cu128, cp313)
torch_url = 'https://download.pytorch.org/whl/cu128/torch-2.10.0%2Bcu128-cp313-cp313-manylinux_2_28_x86_64.whl'
dest = os.path.join(out, 'torch-2.10.0+cu128-cp313-cp313-manylinux_2_28_x86_64.whl')
if not os.path.exists(dest):
    print('Downloading torch...')
    try:
        urllib.request.urlretrieve(torch_url, dest)
        print('torch downloaded:', os.path.getsize(dest))
    except Exception as e:
        print('torch urllib failed:', repr(e))

deps = ['xgrammar', 'msgspec', 'cbor2', 'compressed-tensors', 'gguf', 'outlines',
        'outlines-core', 'llguidance', 'lm-format-enforcer', 'partial-json-parser',
        'mistral-common', 'pyzmq', 'vllm==0.19.1']

for pkg in deps:
    print('=== downloading', pkg, '===')
    r = subprocess.run([sys.executable, '-m', 'pip', 'download', '-q', '--dest', out,
                        '--only-binary=:all:', pkg], check=False, capture_output=True, text=True)
    print('rc:', r.returncode)
    if r.returncode != 0:
        print('stderr:', r.stderr[-500:])

print('EXTRA_WHEELS total:', len(glob.glob(out + '/*.whl')))
for w in sorted(glob.glob(out + '/*.whl')):
    print('  ', os.path.basename(w))

# Verify: dedupe wheels by distribution name to avoid version conflicts
print('Installing wheels for verification (deduped)...')
import re as _re
seen = {}
for w in sorted(glob.glob(out + '/*.whl')):
    base = os.path.basename(w)
    dist = base.split('-')[0].lower().replace('_','-')
    seen[dist] = w
deduped = list(seen.values())
print('deduped wheels:', len(deduped))
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-index', '--no-deps', '--force-reinstall'] + deduped, check=False)

print('Running vLLM --help verification...')
r = subprocess.run([sys.executable, '-m', 'vllm.entrypoints.openai.api_server', '--help'],
                   capture_output=True, text=True, timeout=300)
print('vllm --help rc:', r.returncode)
combined = (r.stdout or '') + (r.stderr or '')
print('stdout tail:', r.stdout[-1000:])
print('stderr tail:', r.stderr[-1000:])
if 'ModuleNotFoundError' in combined:
    print('VERIFY FAILED: ModuleNotFoundError present')
else:
    if r.returncode == 0:
        print('VERIFY OK: vLLM --help succeeded, no ModuleNotFoundError')
    else:
        print('VERIFY: no ModuleNotFoundError string but rc != 0')

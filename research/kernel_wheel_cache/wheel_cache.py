import os, sys, urllib.request, glob
print('PYTHON:', sys.version)
out = '/kaggle/working/extra_wheels'
os.makedirs(out, exist_ok=True)

# Download torch 2.10.0
torch_url = 'https://download.pytorch.org/whl/cu128/torch-2.10.0%2Bcu128-cp313-cp313-manylinux_2_28_x86_64.whl'
dest = os.path.join(out, 'torch-2.10.0+cu128-cp313-cp313-manylinux_2_28_x86_64.whl')
if not os.path.exists(dest):
    print('Downloading torch...')
    urllib.request.urlretrieve(torch_url, dest)
    print('torch downloaded:', os.path.getsize(dest))

# Download cbor2 from PyPI
import subprocess
subprocess.run([sys.executable, '-m', 'pip', 'download', '-q', '--dest', out, 'cbor2'], check=False)

print('EXTRA_WHEELS torch:', glob.glob(out + '/torch-2.10.0*.whl'))
print('EXTRA_WHEELS cbor2:', glob.glob(out + '/cbor2*.whl'))

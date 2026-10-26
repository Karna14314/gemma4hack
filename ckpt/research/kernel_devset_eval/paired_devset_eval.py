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
    if False and WHEELHOUSE_DIR is not None and WHEELHOUSE_DIR.exists():
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
        wheels = sorted(str(w) for w in tmp_whl.glob('*.whl'))
        print(f'Installing {len(wheels)} wheels from {WHEELHOUSE_DIR}...')
        subprocess.run([sys.executable,'-m','pip','install','-q','--no-deps','--force-reinstall',*wheels], check=True)
        _importlib.invalidate_caches()
        print('Wheelhouse installation complete.')
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
    for cand in [WORKING_DIR / 'bundles' / name,
                 Path('/kaggle/working') / 'bundles' / name,
                 Path(__file__).resolve().parent / 'bundles' / name]:
        if (cand / 'agent.yaml').exists():
            return cand
    # search
    for p in Path('/kaggle/working').rglob('agent.yaml'):
        if name in str(p):
            return p.parent
    raise FileNotFoundError(name)

BUNDLE_MAP = {
    'exp05': find_bundle('exp05_patch_integrity'),
    'exp10-consolidated': find_bundle('exp10_consolidated'),
}

# Load tasks
tasks = [json.loads(x) for x in open(DATA_DIR / 'tasks.jsonl') if x.strip()]
task_by_id = {t['instance_id']: t for t in tasks}

# Load selected 24
sel_path = None
for cand in [Path(__file__).resolve().parent / 'eval_24_tasks.json',
             WORKING_DIR / 'eval_24_tasks.json']:
    if cand.exists():
        sel_path = cand
        break
assert sel_path is not None, 'eval_24_tasks.json not found'
selected_ids = json.load(open(sel_path))['instance_ids']
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

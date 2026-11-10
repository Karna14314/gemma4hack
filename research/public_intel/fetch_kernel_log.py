"""Fetch a kernel's log via the Kaggle REST client and print its tail + markers."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))
import kaggle_rest  # noqa: E402

ref = sys.argv[1]
owner, slug = kaggle_rest.split_ref(ref)
status, payload, _ = kaggle_rest.request(
    "GET", f"/api/v1/kernels/output?userName={owner}&kernelSlug={slug}&pageSize=200"
)
body = json.loads(payload.decode("utf-8"), strict=False)
log = body.get("logNullable") or ""
entries = json.loads(log)
print(f"log entries: {len(entries)}")
print("--- tail 45 ---")
for e in entries[-45:]:
    print(f"[{e.get('stream_name')}] {e.get('data','').rstrip()}")

print("\n--- markers (Traceback / DONE_OK / error) ---")
for e in entries:
    d = e.get("data", "")
    if any(k in d for k in ("Traceback", "DONE_OK", "Error", "ERROR", "error:")):
        print(f"[{e.get('stream_name')}] {d.rstrip()}")

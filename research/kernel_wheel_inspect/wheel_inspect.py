import os, glob
print("Looking for wheels/adk/swegemma...")
for root in ["/kaggle", "/opt", "/usr", "/"]:
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".whl") or "adk_submission" in fn or "swegemma" in fn:
                print(os.path.join(dirpath, fn))
        # prune deep
        if dirpath.count(os.sep) > 6:
            dirnames[:] = []
print("DONE")

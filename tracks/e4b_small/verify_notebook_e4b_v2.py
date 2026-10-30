#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
import zipfile
import json
import yaml
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[2]
    bundle = root / "tracks" / "e4b_small" / "bundles" / "e4b_v2"
    builder = root / "tools" / "build_notebook.py"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_nb = Path(tmpdir) / "submission_notebook.ipynb"
        r = subprocess.run(
            [sys.executable, str(builder), "--bundle", str(bundle), "--out", str(tmp_nb)],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print("Failed to build notebook:")
            print(r.stderr)
            sys.exit(1)

        nb_text = tmp_nb.read_text()
        assert "gemma-4-31b" not in nb_text, "gemma-4-31b leaked into notebook script"
        assert "FALLBACK" not in nb_text, "FALLBACK leaked into notebook script"

        # Run the notebook in tempdir to test execution and check generated submission.zip
        # Executing python cells from notebook or running jupyter nbconvert / python script
        # Let's extract code cells and execute them in tmpdir context
        import nbformat
        nb = nbformat.read(str(tmp_nb), as_version=4)

        os.chdir(tmpdir)
        # Execute code cells in a fresh globals dict
        exec_globals = {"__file__": str(tmp_nb)}
        for idx, cell in enumerate(nb.cells):
            if cell.cell_type == "code":
                try:
                    exec(cell.source, exec_globals)
                except Exception as e:
                    print(f"Cell {idx} failed: {e}")
                    raise

        # Look for submission.zip in working directory (tmpdir if we cd'd, or relative)
        # Check submission.zip and submission_manifest.json produced by notebook
        zip_path = Path("submission.zip")
        manifest_path = Path("submission_manifest.json")
        assert zip_path.is_file(), "submission.zip not generated!"
        assert manifest_path.is_file(), "submission_manifest.json not generated!"

        manifest = json.loads(manifest_path.read_text())
        print("Generated manifest:", json.dumps(manifest, indent=2))
        assert manifest.get("selected_package") == "primary", f"Expected primary package, got {manifest.get('selected_package')}"

        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()
            assert "agent.yaml" in names, "agent.yaml missing from submission.zip"
            class _IncludeLoader(yaml.SafeLoader):
                pass
            _IncludeLoader.add_constructor("!include", lambda loader, node: loader.construct_scalar(node))
            agent_yaml = yaml.load(z.read("agent.yaml").decode("utf-8"), Loader=_IncludeLoader)
            print("Zip agent.yaml:", agent_yaml)
            assert agent_yaml.get("model") == "gemma-4-e4b-it-qat-w4a16-ct", f"Expected gemma-4-e4b-it-qat-w4a16-ct, got {agent_yaml.get('model')}"
            assert agent_yaml.get("name") == "swe_agent", f"Expected swe_agent, got {agent_yaml.get('name')}"

        print("LOCAL E4B NOTEBOOK VERIFICATION ALL CHECKS PASSED!")

if __name__ == "__main__":
    main()

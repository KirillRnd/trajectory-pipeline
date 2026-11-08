"""Code-only import. Run in Docker; write to runs/, then review before copying.

No imported script or notebook is executed. Formula definitions are selected
explicitly; training, file reads, integrations and plotting are not imported.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil


EXCLUDED = {
    "final_qa_preprint.py": "article QA",
    "generate_c_artifacts.py": "article figures and tables",
    "ConvertFormula.py": "formula-to-LaTeX article helper",
}
FORMULAS = {
    "l1": ("L1_approx.py", {"mu", "L1", "x1_fun", "x2_fun"}),
    "l2": ("L2_approx.py", {"mu", "L2", "x1_fun", "x2_fun"}),
    "l3": ("L3_approx.py", {"mu", "x1_fun", "x2_fun"}),
    "l4_v2": ("L4_approx_v2.py", {"mu", "x1", "x2"}),
    "l4_v3": ("L4_approx_v3.py", {"mu", "x1", "x2"}),
    "s3": ("S3_approx_2D.py", {"mu0"}),
}
FUNCTIONS = {"odeCR3BP", "x1_fun", "x2_fun", "v1_fun", "v2_fun", "T_fun", "v1", "v2", "T"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_formulas(source, constants):
    text = source.read_text(encoding="utf-8-sig")
    segments = []
    for node in ast.parse(text).body:
        selected = isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS
        if isinstance(node, ast.Assign):
            names = {n.id for n in node.targets if isinstance(n, ast.Name)}
            selected = bool(names) and names <= constants
        if selected:
            segments.append(ast.get_source_segment(text, node))
    return (f'"""Definitions extracted unchanged from source/{source.name}."""\n'
            "import math\nimport numpy as np\n\n" + "\n\n".join(segments) + "\n")


def import_source(source, output):
    output.mkdir(parents=True, exist_ok=False)
    for folder in ("source", "notebooks", "approximations"):
        (output / folder).mkdir()
    manifest = {"original_root": str(source), "policy": "code only; no datasets, articles, images or cell outputs",
                "excluded_python": EXCLUDED, "files": [], "generated": []}
    for src in sorted(source.glob("*.py")):
        if src.name in EXCLUDED:
            continue
        dest = output / "source" / src.name
        shutil.copyfile(src, dest)
        manifest["files"].append({"source": src.name, "path": str(dest.relative_to(output)),
                                  "source_sha256": sha(src), "sha256": sha(dest), "transform": "byte copy"})
    for src in sorted(source.glob("*.ipynb")):
        original = json.loads(src.read_text(encoding="utf-8-sig"))
        cells = [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": c["source"]}
                 for c in original.get("cells", []) if c["cell_type"] == "code" and "".join(c["source"]).strip()]
        if not cells:
            continue
        dest = output / "notebooks" / src.name
        dest.write_text(json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 4},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        manifest["files"].append({"source": src.name, "path": str(dest.relative_to(output)),
                                  "source_sha256": sha(src), "sha256": sha(dest),
                                  "transform": "nonempty code cells only; source preserved; no metadata or outputs",
                                  "code_cells": len(cells)})
    for name, (filename, constants) in FORMULAS.items():
        dest = output / "approximations" / (name + ".py")
        dest.write_text(extract_formulas(source / filename, constants), encoding="utf-8")
        manifest["generated"].append({"path": str(dest.relative_to(output)), "source": filename, "sha256": sha(dest)})
    dest = output / "approximations" / "c_families.py"
    shutil.copyfile(source / "formulas.py", dest)
    manifest["generated"].append({"path": str(dest.relative_to(output)), "source": "formulas.py", "sha256": sha(dest)})
    (output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(manifest["files"]), "formula_modules": len(manifest["generated"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    import_source(args.source, args.output)

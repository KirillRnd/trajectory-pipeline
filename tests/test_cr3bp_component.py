import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from components.cr3bp.import_source import FORMULAS, extract_formulas
from trajectory_pipeline.cr3bp import seed


ROOT = Path(__file__).resolve().parents[1] / "components" / "cr3bp"


class CR3BPComponentTest(unittest.TestCase):
    def test_import_provenance_and_code_only_notebooks(self):
        manifest = json.loads((ROOT / "source_manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["files"] + manifest["generated"]:
            path = ROOT / entry["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"], str(path))
            if entry.get("transform") == "byte copy":
                self.assertEqual(entry["sha256"], entry["source_sha256"])
            if path.suffix == ".ipynb":
                notebook = json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(notebook["metadata"])
                for cell in notebook["cells"]:
                    self.assertEqual(cell["cell_type"], "code")
                    self.assertFalse(cell["outputs"])
                    self.assertIsNone(cell["execution_count"])
                    self.assertFalse(cell["metadata"])

    def test_extraction_preserves_source_definitions(self):
        for name, (filename, constants) in FORMULAS.items():
            self.assertEqual((ROOT / "approximations" / (name + ".py")).read_text(encoding="utf-8"),
                             extract_formulas(ROOT / "source" / filename, constants))
        self.assertEqual((ROOT / "source/formulas.py").read_bytes(), (ROOT / "approximations/c_families.py").read_bytes())

    def test_family_guards_and_explicit_approximation_status(self):
        for family, parameter in [("L1", .8), ("L2", 1.2), ("L3", -1.3), ("L4_v2", 1.), ("L4_v3", 1.), ("S3", 1.)]:
            result = seed(family, parameter)
            self.assertEqual(result["status"], "approximation_only")
            self.assertEqual(result["frame"], "rotating_barycentric")
            self.assertEqual(result["units"], "normalized")
            self.assertTrue(np.all(np.isfinite(result["state_xy_vxvy"])))
            self.assertGreater(result["period"], 0)
            with self.assertRaisesRegex(ValueError, "unsupported mu"):
                seed(family, parameter, mu=3e-6)
            with self.assertRaisesRegex(ValueError, "outside source"):
                seed(family, 100.)
        with self.assertRaises(ValueError):
            seed("L1", float("nan"))
        with self.assertRaises(ValueError):
            seed("unknown", 1.)

    def test_representative_propagation(self):
        from components.cr3bp.check_approximations import check
        for row in check()["rows"]:
            self.assertTrue(row["integration_success"], row["family"])
            self.assertLess(row["jacobi_max_drift"], 1e-8, row["family"])
            self.assertFalse(row["accepted_as_periodic_orbit"])


if __name__ == "__main__":
    unittest.main()

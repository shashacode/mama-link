"""Run local checks and write the synthetic evaluation report."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mama_link.__main__ import evaluate

suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
report = evaluate()
(ROOT / "docs/evaluation-latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"Evaluation: {report['matches']}/{report['cases']} labels; {report['emergencies_detected']}/{report['expected_emergencies']} emergencies.")
raise SystemExit(0 if result.wasSuccessful() else 1)

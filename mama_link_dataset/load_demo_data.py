"""
MAMA-Link synthetic dataset helper.
This is software-demo code, not a clinical triage protocol.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def load_cases(runtime_safe=True):
    name = "maternal_data_runtime.json" if runtime_safe else "maternal_data.json"
    path = ROOT / "maternal" / "challenge-1-build" / name
    return json.loads(path.read_text(encoding="utf-8"))["cases"]

def load_facilities():
    path = ROOT / "maternal" / "data" / "facilities.json"
    return json.loads(path.read_text(encoding="utf-8"))["facilities"]

def load_resources():
    path = ROOT / "maternal" / "data" / "support_resources.json"
    return json.loads(path.read_text(encoding="utf-8"))["resources"]

if __name__ == "__main__":
    print(f"Runtime cases: {len(load_cases())}")
    print(f"Facilities: {len(load_facilities())}")
    print(f"Resources: {len(load_resources())}")

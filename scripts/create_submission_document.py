"""Compatibility entry point for the canonical MAMA-Link submission document."""

from pathlib import Path
from shutil import copy2

from build_submission_document import OUTPUT, build_document


ROOT = Path(__file__).resolve().parents[1]
LEGACY_OUTPUT = ROOT / "deliverables" / "MAMA-Link-Hackathon-Submission.docx"


if __name__ == "__main__":
    build_document()
    copy2(OUTPUT, LEGACY_OUTPUT)
    print(LEGACY_OUTPUT)

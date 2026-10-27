"""Test runner script for Beyond Horizons."""
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

if __name__ == "__main__":
    print("=" * 70)
    print("  BEYOND HORIZONS — SMART TRAVEL MANAGEMENT SYSTEM")
    print("  AUTOMATED TEST SUITE EXECUTION")
    print("=" * 70)

    # Run pytest on the tests directory
    args = [
        "-v",
        "--tb=short",
        "tests"
    ]
    exit_code = pytest.main(args)
    sys.exit(exit_code)

"""Compatibility entry point; all API launches now share config/runtime.json."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_chat import main

if __name__ == '__main__':
    main()

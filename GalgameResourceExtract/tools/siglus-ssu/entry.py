import multiprocessing
from pathlib import Path
import sys

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))

from archive_cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())

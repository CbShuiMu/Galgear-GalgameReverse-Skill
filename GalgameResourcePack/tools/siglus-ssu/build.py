"""Build with Python 3.12+ and PyInstaller 6.21.0; never downloads at runtime."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True,
                        help="new build workspace outside the tool directory")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("Python 3.12+ is required")
    root = Path(__file__).resolve().parent
    output = args.output.resolve()
    if output == root or root in output.parents:
        parser.error("build workspace must be outside the tool directory")
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
               "--onefile", "--console", "--noupx", "--name", "siglus-ssu",
               "--paths", str(root / "source"), "--paths", str(root),
               "--collect-submodules", "siglus_ssu",
               "--add-data", str(root / "source" / "siglus_ssu-0.5.7.dist-info")
               + ";siglus_ssu-0.5.7.dist-info",
               "--add-data", str(root / "source" / "siglus_ssu" / "const.py")
               + ";siglus_ssu",
               "--exclude-module", "PIL", "--exclude-module", "psutil",
               "--exclude-module", "tkinter",
               "--distpath", str(output / "dist"),
               "--workpath", str(output / "work"),
               "--specpath", str(output)]
    # Upstream dispatches CLI modes with import_module; enumerate them so that
    # an isolated Python distribution also finds every dynamic CLI entry.
    for module in sorted((root / "source" / "siglus_ssu").glob("*.py")):
        if module.stem != "__init__":
            command.extend(["--hidden-import", "siglus_ssu." + module.stem])
    command.append(str(root / "entry.py"))
    return subprocess.call(command, cwd=output)


if __name__ == "__main__":
    raise SystemExit(main())

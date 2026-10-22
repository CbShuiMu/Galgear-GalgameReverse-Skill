"""Rebuild the console bundle from the corresponding sources (Python 3.12)."""
from pathlib import Path
import subprocess
import sys

source = Path(__file__).resolve().parent
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                '--onedir', '--console', '--name', 'ethornell',
                '--distpath', str(source/'dist'), '--workpath', str(source/'build'),
                '--specpath', str(source), str(source/'ethornell.py')], check=True)

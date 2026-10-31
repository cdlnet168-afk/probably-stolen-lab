import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parent
os.chdir(p)
runpy.run_path(str(p/"server.py"),run_name="__main__")

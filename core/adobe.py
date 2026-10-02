from pathlib import Path
import os,subprocess
def launch(executable,photo=None):
    if not executable or not Path(executable).exists(): raise FileNotFoundError("Adobe executable is not configured or was not found.")
    return subprocess.Popen([str(executable)]+([str(photo)] if photo else []))
def guess_apps():
    roots=[Path(os.environ.get("ProgramFiles","C:/Program Files")),Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))]; out={"photoshop":"","lightroom":""}
    for root in roots:
        if root.exists():
            if not out["photoshop"]:
                for p in root.rglob("Photoshop.exe"): out["photoshop"]=str(p); break
            if not out["lightroom"]:
                for p in root.rglob("Lightroom.exe"): out["lightroom"]=str(p); break
    return out

from pathlib import Path
import shutil
from .scanner import sha256_file
def safe_destination(root,event_name):
    root=Path(root).resolve()
    if root.drive.upper()=="C:": raise ValueError("OptiSys will not use C: as a photo destination.")
    event=root/event_name
    for sub in ("01_ORIGINALS","02_SELECTS","03_EDITS","04_EXPORTS","05_DELIVERY"): (event/sub).mkdir(parents=True,exist_ok=True)
    return event
def verified_copy(src,dst):
    src,dst=Path(src),Path(dst); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    if sha256_file(src)!=sha256_file(dst): dst.unlink(missing_ok=True); raise IOError(f"Verification failed: {src}")
    return dst

from pathlib import Path
from PIL import Image
from config import CACHE_DIR
import hashlib
def thumbnail(path,size=(220,160)):
    p=Path(path); key=str(p)+str(p.stat().st_mtime_ns)+str(size)
    out=CACHE_DIR/(hashlib.sha1(key.encode()).hexdigest()+".jpg")
    if out.exists(): return out
    try:
        with Image.open(p) as im:
            im.thumbnail(size,Image.Resampling.LANCZOS)
            canvas=Image.new("RGB",size,"#111")
            canvas.paste(im.convert("RGB"),((size[0]-im.width)//2,(size[1]-im.height)//2))
            canvas.save(out,"JPEG",quality=88)
            return out
    except Exception:return None

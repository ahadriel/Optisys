from pathlib import Path
import hashlib
from PIL import Image,ExifTags
RAW={".cr2",".cr3",".nef",".arw",".dng",".raf",".rw2",".orf",".srw",".pef",".raw"}
IMAGE=RAW|{".jpg",".jpeg",".png",".tif",".tiff",".webp",".bmp",".heic",".heif"}
def sha256_file(path,chunk=1024*1024):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while b:=f.read(chunk): h.update(b)
    return h.hexdigest()
def read_meta(path,do_hash=True):
    p=Path(path); m={"path":str(p.resolve()),"filename":p.name,"ext":p.suffix.lower(),"size":p.stat().st_size}
    if do_hash: m["sha256"]=sha256_file(p)
    if m["ext"] in RAW: return m
    try:
        with Image.open(p) as im:
            m["width"],m["height"]=im.size; tags={ExifTags.TAGS.get(k,k):v for k,v in im.getexif().items()}
            m["camera"]=str(tags.get("Model","")); m["lens"]=str(tags.get("LensModel","")); m["taken_at"]=str(tags.get("DateTimeOriginal") or tags.get("DateTime") or "")
            m["iso"]=int(tags["ISOSpeedRatings"]) if tags.get("ISOSpeedRatings") else None
            m["aperture"]=float(tags["FNumber"]) if tags.get("FNumber") else None; m["shutter"]=str(tags.get("ExposureTime",""))
    except Exception as e: m["error"]=str(e)
    return m
def discover(root):
    for p in Path(root).rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE: yield p

import sqlite3
from pathlib import Path
from datetime import datetime
SCHEMA="""CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,client TEXT DEFAULT '',date TEXT DEFAULT '',root TEXT DEFAULT '',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY,event_id INTEGER NOT NULL,path TEXT NOT NULL UNIQUE,filename TEXT NOT NULL,ext TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT,width INTEGER,height INTEGER,camera TEXT,lens TEXT,taken_at TEXT,iso INTEGER,aperture REAL,shutter TEXT,rating INTEGER DEFAULT 0,rejected INTEGER DEFAULT 0,note TEXT DEFAULT '',imported_at TEXT NOT NULL,FOREIGN KEY(event_id) REFERENCES events(id));
CREATE INDEX IF NOT EXISTS idx_photos_event ON photos(event_id);CREATE INDEX IF NOT EXISTS idx_photos_hash ON photos(sha256);"""
class Database:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.con=sqlite3.connect(self.path); self.con.row_factory=sqlite3.Row; self.con.executescript(SCHEMA); self.con.commit()
    def events(self): return self.con.execute("SELECT * FROM events ORDER BY created_at DESC").fetchall()
    def create_event(self,name,client="",date="",root=""):
        self.con.execute("INSERT OR IGNORE INTO events(name,client,date,root,created_at) VALUES(?,?,?,?,?)",(name,client,date,root,datetime.now().isoformat(timespec="seconds"))); self.con.commit()
        return self.con.execute("SELECT * FROM events WHERE name=?",(name,)).fetchone()
    def add_photo(self,event_id,m):
        self.con.execute("""INSERT OR REPLACE INTO photos(event_id,path,filename,ext,size,sha256,width,height,camera,lens,taken_at,iso,aperture,shutter,rating,rejected,note,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (event_id,m["path"],m["filename"],m["ext"],m["size"],m.get("sha256"),m.get("width"),m.get("height"),m.get("camera"),m.get("lens"),m.get("taken_at"),m.get("iso"),m.get("aperture"),m.get("shutter"),m.get("rating",0),m.get("rejected",0),m.get("note",""),datetime.now().isoformat(timespec="seconds"))); self.con.commit()
    def photos(self,event_id,query="",mode="all"):
        sql="SELECT * FROM photos WHERE event_id=?"; args=[event_id]
        if query: sql+=" AND (filename LIKE ? OR camera LIKE ? OR lens LIKE ? OR path LIKE ?)"; q=f"%{query}%"; args += [q,q,q,q]
        if mode=="raw": sql+=" AND ext IN ('.cr2','.cr3','.nef','.arw','.dng','.raf','.rw2','.orf','.srw','.pef','.raw')"
        elif mode=="jpeg": sql+=" AND ext IN ('.jpg','.jpeg')"
        elif mode=="rated": sql+=" AND rating>0"
        elif mode=="rejected": sql+=" AND rejected=1"
        return self.con.execute(sql+" ORDER BY taken_at,filename",args).fetchall()
    def update_photo(self,pid,**fields):
        allowed={"rating","rejected","note"}; fields={k:v for k,v in fields.items() if k in allowed}
        if fields: self.con.execute("UPDATE photos SET "+",".join(f"{k}=?" for k in fields)+" WHERE id=? ",(*fields.values(),pid)); self.con.commit()
    def hashes(self,event_id): return {r[0] for r in self.con.execute("SELECT sha256 FROM photos WHERE event_id=? AND sha256 IS NOT NULL",(event_id,))}
    def close(self): self.con.close()

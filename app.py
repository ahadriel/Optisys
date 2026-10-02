import sys,os,hashlib,sqlite3,csv,shutil,subprocess,json
from pathlib import Path
from datetime import datetime
from PIL import Image,ImageOps,ExifTags
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QPixmap,QKeySequence,QAction,QIcon
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QListWidget,QListWidgetItem,QLabel,QPushButton,QLineEdit,QComboBox,QProgressBar,QTextEdit,QMessageBox,QFileDialog,QInputDialog,QDialog,QFormLayout,QDialogButtonBox

VERSION="27.1.0"; ROOT=Path(os.environ.get("APPDATA",str(Path.home())))/"OptiSys"; ROOT.mkdir(parents=True,exist_ok=True); DB=ROOT/"optisys.sqlite3"; CACHE=ROOT/"cache"; CACHE.mkdir(exist_ok=True)
RAW={".cr2",".cr3",".nef",".arw",".dng",".raf",".rw2",".orf",".srw",".pef",".raw",".3fr",".iiq"}; IMG=RAW|{".jpg",".jpeg",".png",".tif",".tiff",".webp",".bmp",".heic",".heif"}
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        while b:=f.read(1024*1024): h.update(b)
    return h.hexdigest()
def meta(path):
    p=Path(path); m={"path":str(p.resolve()),"filename":p.name,"ext":p.suffix.lower(),"size":p.stat().st_size,"sha256":sha(p)}
    try:
        with Image.open(p) as im:
            m["width"],m["height"]=im.size; t={ExifTags.TAGS.get(k,k):v for k,v in im.getexif().items()}
            m.update(camera=str(t.get("Model","")),lens=str(t.get("LensModel","")),taken=str(t.get("DateTimeOriginal") or t.get("DateTime") or ""),iso=str(t.get("ISOSpeedRatings","")),aperture=str(t.get("FNumber","")),shutter=str(t.get("ExposureTime","")))
    except: pass
    return m
class Store:
    def __init__(self):
        self.c=sqlite3.connect(DB); self.c.row_factory=sqlite3.Row
        self.c.executescript("""CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,name TEXT UNIQUE,client TEXT,date TEXT,root TEXT,created TEXT);
CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY,event INTEGER,path TEXT UNIQUE,filename TEXT,ext TEXT,size INTEGER,sha256 TEXT,width INTEGER,height INTEGER,camera TEXT,lens TEXT,taken TEXT,iso TEXT,aperture TEXT,shutter TEXT,rating INTEGER DEFAULT 0,rejected INTEGER DEFAULT 0,note TEXT DEFAULT '',verified INTEGER DEFAULT 0,created TEXT,FOREIGN KEY(event) REFERENCES events(id));
CREATE INDEX IF NOT EXISTS ih ON photos(event,sha256);"""); self.c.commit()
    def events(self): return self.c.execute("SELECT * FROM events ORDER BY created DESC").fetchall()
    def event(self,i): return self.c.execute("SELECT * FROM events WHERE id=?",(i,)).fetchone()
    def new_event(self,n,c,d):
        self.c.execute("INSERT OR IGNORE INTO events VALUES(NULL,?,?,?,?,?)",(n,c,d,"",datetime.now().isoformat(timespec="seconds"))); self.c.commit(); return self.c.execute("SELECT * FROM events WHERE name=?",(n,)).fetchone()
    def add(self,e,m,v=0):
        self.c.execute("""INSERT OR IGNORE INTO photos(event,path,filename,ext,size,sha256,width,height,camera,lens,taken,iso,aperture,shutter,rating,rejected,note,verified,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(e,m["path"],m["filename"],m["ext"],m["size"],m["sha256"],m.get("width"),m.get("height"),m.get("camera",""),m.get("lens",""),m.get("taken",""),m.get("iso",""),m.get("aperture",""),m.get("shutter",""),0,0,"",v,datetime.now().isoformat(timespec="seconds"))); self.c.commit()
    def rows(self,e,q="",mode="ALL",sort="taken"):
        s="SELECT * FROM photos WHERE event=?"; a=[e]
        if q: s+=" AND (filename LIKE ? OR camera LIKE ? OR lens LIKE ? OR path LIKE ?)"; z="%"+q+"%"; a += [z,z,z,z]
        if mode=="RAW": s+=" AND ext IN ("+",".join("'"+x+"'" for x in RAW)+")"
        elif mode=="JPEG": s+=" AND ext IN ('.jpg','.jpeg')"
        elif mode=="RATED": s+=" AND rating>0"
        elif mode=="REJECTED": s+=" AND rejected=1"
        elif mode=="UNRATED": s+=" AND rating=0 AND rejected=0"
        return self.c.execute(s+" ORDER BY "+("taken,filename" if sort=="taken" else "filename"),a).fetchall()
    def update(self,i,**kw):
        kw={k:v for k,v in kw.items() if k in {"rating","rejected","note","verified"}}
        if kw: self.c.execute("UPDATE photos SET "+",".join(k+"=?" for k in kw)+" WHERE id=?",(*kw.values(),i)); self.c.commit()
    def close(self): self.c.close()
class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("OptiSys v"+VERSION+" — Event Photography Workstation"); self.resize(1550,920); self.db=Store(); self.event_id=None; self.rows=[]; self.current=None; self.settings=self.load_settings(); self.build(); self.load_events()
    def load_settings(self):
        try:return json.loads((ROOT/"settings.json").read_text())
        except:return {"photoshop":"","lightroom":"","last_import":""}
    def save_settings(self):(ROOT/"settings.json").write_text(json.dumps(self.settings,indent=2))
    def build(self):
        self.setStyleSheet("QMainWindow,QWidget{background:#0e1116;color:#e6e9ee;font-family:Segoe UI}QPushButton,QLineEdit,QComboBox,QTextEdit{background:#181d24;color:#e6e9ee;border:1px solid #303844;border-radius:6px;padding:7px}QPushButton:hover{background:#252c36}QListWidget{background:#090c10;border:1px solid #2a3038}QListWidget::item:selected{background:#263242}QProgressBar{border:1px solid #303844;border-radius:5px;text-align:center}QProgressBar::chunk{background:#73849c}")
        root=QWidget(); self.setCentralWidget(root); v=QVBoxLayout(root); h=QHBoxLayout(); h.addWidget(QLabel("<h2>OPTISYS</h2> <span style='color:#7f8b9d'>WORKSTATION v"+VERSION+"</span>")); h.addStretch()
        self.events=QComboBox(); self.events.currentIndexChanged.connect(self.change_event); h.addWidget(QLabel("EVENT")); h.addWidget(self.events); b=QPushButton("+ EVENT"); b.clicked.connect(self.new_event); h.addWidget(b); v.addLayout(h)
        bar=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText("Search filename, camera, lens, path…"); self.search.textChanged.connect(self.refresh); bar.addWidget(self.search,3)
        self.mode=QComboBox(); self.mode.addItems(["ALL","RAW","JPEG","RATED","REJECTED","UNRATED"]); self.mode.currentTextChanged.connect(self.refresh); bar.addWidget(self.mode)
        self.sort=QComboBox(); self.sort.addItems(["taken","filename"]); self.sort.currentTextChanged.connect(self.refresh); bar.addWidget(self.sort)
        for txt,fn in [("IMPORT",self.import_folder),("VERIFY",self.verify_event),("EXPORT",self.export),("CONTACT SHEET",self.contact),("REPORT",self.report),("SETTINGS",self.settings_dialog)]: q=QPushButton(txt); q.clicked.connect(fn); bar.addWidget(q)
        v.addLayout(bar); sp=QSplitter(Qt.Horizontal); v.addWidget(sp,1)
        left=QWidget(); lv=QVBoxLayout(left); self.list=QListWidget(); self.list.setIconSize(QSize(180,125)); self.list.currentItemChanged.connect(self.select); lv.addWidget(self.list); self.progress=QProgressBar(); self.progress.hide(); lv.addWidget(self.progress); sp.addWidget(left)
        right=QWidget(); rv=QVBoxLayout(right); self.preview=QLabel("Select a photograph"); self.preview.setAlignment(Qt.AlignCenter); rv.addWidget(self.preview,3); self.info=QTextEdit(); self.info.setReadOnly(True); rv.addWidget(self.info,2)
        ctl=QHBoxLayout()
        for txt,fn in [("★5",lambda:self.rate(5)),("★4",lambda:self.rate(4)),("★3",lambda:self.rate(3)),("★2",lambda:self.rate(2)),("★1",lambda:self.rate(1)),("REJECT",self.reject),("CLEAR",self.clear),("PHOTOSHOP",lambda:self.adobe("photoshop")),("LIGHTROOM",lambda:self.adobe("lightroom")),("FOLDER",self.folder)]: q=QPushButton(txt); q.clicked.connect(fn); ctl.addWidget(q)
        rv.addLayout(ctl); sp.addWidget(right); sp.setSizes([700,850]); self.shortcuts(); self.statusBar().showMessage("Ready — local only")
    def shortcuts(self):
        for k,fn in [("1",lambda:self.rate(1)),("2",lambda:self.rate(2)),("3",lambda:self.rate(3)),("4",lambda:self.rate(4)),("5",lambda:self.rate(5)),("X",self.reject),("0",self.clear),("Right",self.next_photo),("Left",self.prev_photo),("Space",self.toggle_reject)]:
            a=QAction(self); a.setShortcut(QKeySequence(k)); a.triggered.connect(fn); self.addAction(a)
    def load_events(self):
        self.events.blockSignals(True); self.events.clear()
        for e in self.db.events(): self.events.addItem(e["name"],e["id"])
        self.events.blockSignals(False)
        if self.events.count(): self.events.setCurrentIndex(0); self.change_event(0)
    def change_event(self,_): self.event_id=self.events.currentData(); self.refresh()
    def new_event(self):
        n,ok=QInputDialog.getText(self,"New event","Event name")
        if not ok or not n.strip(): return
        c,_=QInputDialog.getText(self,"Client","Client (optional)"); d,_=QInputDialog.getText(self,"Date","Date YYYY-MM-DD (optional)"); e=self.db.new_event(n.strip(),c,d); self.load_events(); self.events.setCurrentText(e["name"])
    def refresh(self):
        self.list.clear(); self.rows=[]; self.current=None
        if not self.event_id:return
        self.rows=self.db.rows(self.event_id,self.search.text().strip(),self.mode.currentText(),self.sort.currentText())
        for r in self.rows:
            it=QListWidgetItem(("★"*r["rating"]+" " if r["rating"] else "")+r["filename"]+("  ✕" if r["rejected"] else "")); it.setData(Qt.UserRole,r["id"]); it.setToolTip(r["path"]); th=self.thumb(r["path"])
            if th:it.setIcon(QIcon(str(th)))
            self.list.addItem(it)
        self.statusBar().showMessage(str(len(self.rows))+" photographs")
    def thumb(self,path):
        p=Path(path)
        if not p.exists() or p.suffix.lower() in RAW:return None
        out=CACHE/(hashlib.sha1((str(p.resolve())+str(p.stat().st_mtime_ns)).encode()).hexdigest()+".jpg")
        if out.exists():return out
        try:
            with Image.open(p) as im:
                im=ImageOps.exif_transpose(im); im.thumbnail((360,250)); im.convert("RGB").save(out,"JPEG",quality=84); return out
        except:return None
    def select(self,cur,_=None):
        if not cur:return
        self.current=next((r for r in self.rows if r["id"]==cur.data(Qt.UserRole)),None); r=self.current
        if not r:return
        p=Path(r["path"])
        if p.suffix.lower() not in RAW and p.exists():
            pix=QPixmap(str(p)); self.preview.setPixmap(pix.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else:self.preview.setText("RAW / preview unavailable in core viewer")
        self.info.setPlainText("\n".join([f"FILE      {r['filename']}",f"PATH      {r['path']}",f"SIZE      {r['size']:,} bytes",f"SHA-256   {r['sha256']}",f"CAMERA    {r['camera'] or '-'}",f"LENS      {r['lens'] or '-'}",f"TAKEN     {r['taken'] or '-'}",f"ISO       {r['iso'] or '-'}",f"APERTURE  {r['aperture'] or '-'}",f"SHUTTER   {r['shutter'] or '-'}",f"RATING    {r['rating']}",f"REJECTED  {bool(r['rejected'])}",f"VERIFIED  {bool(r['verified'])}",f"NOTE      {r['note'] or '-'}"]))
    def rate(self,n):
        if self.current:self.db.update(self.current["id"],rating=n,rejected=0); self.refresh()
    def reject(self):
        if self.current:self.db.update(self.current["id"],rejected=1); self.refresh()
    def clear(self):
        if self.current:self.db.update(self.current["id"],rating=0,rejected=0); self.refresh()
    def toggle_reject(self):
        if self.current:self.db.update(self.current["id"],rejected=0 if self.current["rejected"] else 1); self.refresh()
    def next_photo(self):
        i=self.list.currentRow()
        if i>=0:self.list.setCurrentRow(min(i+1,self.list.count()-1))
    def prev_photo(self):
        i=self.list.currentRow()
        if i>0:self.list.setCurrentRow(i-1)
    def folder(self):
        if self.current:os.startfile(str(Path(self.current["path"]).parent))
    def adobe(self,key):
        if not self.current:return
        p=self.settings.get(key,"")
        if not p or not Path(p).exists():p=QFileDialog.getOpenFileName(self,"Select "+key.title()+" executable",filter="Executable (*.exe)")[0]
        if not p:return
        self.settings[key]=p; self.save_settings()
        try:subprocess.Popen([p,self.current["path"]])
        except Exception as e:QMessageBox.warning(self,"Adobe",str(e))
    def import_folder(self):
        if not self.event_id:return QMessageBox.warning(self,"OptiSys","Create an event first.")
        src=QFileDialog.getExistingDirectory(self,"Select camera card / source",self.settings.get("last_import",""))
        if not src:return
        self.settings["last_import"]=src; self.save_settings(); files=[p for p in Path(src).rglob("*") if p.is_file() and p.suffix.lower() in IMG]
        if not files:return QMessageBox.information(self,"Import","No supported photographs found.")
        copy=QMessageBox.question(self,"Verified ingest","Copy into an OptiSys Originals folder? Yes = verified copy. No = catalog in place.",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes; dest=None
        if copy:
            d=QFileDialog.getExistingDirectory(self,"Choose destination (C: blocked)")
            if not d:return
            if Path(d).resolve().drive.upper()=="C:":return QMessageBox.warning(self,"Blocked","OptiSys will not use C: as a photo destination.")
            dest=Path(d)/self.db.event(self.event_id)["name"]/"01_ORIGINALS"; dest.mkdir(parents=True,exist_ok=True)
        self.progress.show(); self.progress.setRange(0,len(files)); seen={r[0] for r in self.db.c.execute("SELECT sha256 FROM photos WHERE event=?",(self.event_id,))}; added=dup=bad=0
        for i,p in enumerate(files,1):
            try:
                m=meta(p)
                if m["sha256"] in seen:dup+=1
                else:
                    if dest:
                        dst=dest/p.name
                        if dst.exists():dst=dest/(p.stem+"_"+m["sha256"][:8]+p.suffix)
                        shutil.copy2(p,dst)
                        if sha(dst)!=m["sha256"]:dst.unlink(missing_ok=True);raise IOError("checksum mismatch")
                        m=meta(dst); self.db.add(self.event_id,m,1)
                    else:self.db.add(self.event_id,m,0)
                    seen.add(m["sha256"]); added+=1
            except:bad+=1
            self.progress.setValue(i); QApplication.processEvents()
        self.progress.hide(); self.refresh(); self.statusBar().showMessage(f"Ingest complete: {added} added | {dup} duplicates | {bad} failed")
    def verify_event(self):
        if not self.event_id:return
        rows=self.db.rows(self.event_id); ok=bad=0; self.progress.show(); self.progress.setRange(0,len(rows))
        for i,r in enumerate(rows,1):
            try:good=Path(r["path"]).exists() and sha(r["path"])==r["sha256"]; self.db.update(r["id"],verified=int(good)); ok+=int(good); bad+=int(not good)
            except:bad+=1
            self.progress.setValue(i); QApplication.processEvents()
        self.progress.hide(); self.refresh(); QMessageBox.information(self,"Verification",f"Verified: {ok}\nFailed/missing: {bad}")
    def export(self):
        if not self.event_id:return
        rows=[r for r in self.db.rows(self.event_id) if r["rating"]>0 and not r["rejected"]]
        if not rows:return QMessageBox.information(self,"Export","No rated non-rejected photographs.")
        d=QFileDialog.getExistingDirectory(self,"Export selects")
        if not d:return
        if Path(d).resolve().drive.upper()=="C:":return QMessageBox.warning(self,"Blocked","C: is blocked.")
        out=Path(d)/(self.db.event(self.event_id)["name"]+"_SELECTS"); out.mkdir(parents=True,exist_ok=True); ok=bad=0
        for r in rows:
            try:
                dst=out/r["filename"]
                if dst.exists():dst=out/(Path(r["filename"]).stem+"_"+r["sha256"][:8]+Path(r["filename"]).suffix)
                shutil.copy2(r["path"],dst)
                if sha(dst)!=r["sha256"]:dst.unlink(missing_ok=True);raise IOError()
                ok+=1
            except:bad+=1
        QMessageBox.information(self,"Export",f"Verified exports: {ok}\nFailed: {bad}\n{out}")
    def contact(self):
        rows=self.rows or (self.db.rows(self.event_id) if self.event_id else [])
        if not rows:return
        out=QFileDialog.getSaveFileName(self,"Save contact sheet","contact_sheet.jpg","JPEG (*.jpg)")[0]
        if not out:return
        from PIL import ImageDraw
        cols=5; cw,ch=230,190; sheet=Image.new("RGB",(cols*cw,((len(rows)+cols-1)//cols)*ch),"#111318"); draw=ImageDraw.Draw(sheet)
        for i,r in enumerate(rows):
            try:
                im=ImageOps.exif_transpose(Image.open(r["path"])); im.thumbnail((210,145)); x=i%cols*cw+(210-im.width)//2; y=i//cols*ch; sheet.paste(im.convert("RGB"),(x,y)); draw.text((i%cols*cw+7,y+150),r["filename"][:27],fill="white")
            except:pass
        sheet.save(out,"JPEG",quality=92); QMessageBox.information(self,"Contact sheet","Saved.")
    def report(self):
        if not self.event_id:return
        out=QFileDialog.getSaveFileName(self,"Save report","optisys_report.csv","CSV (*.csv)")[0]
        if not out:return
        rows=self.db.rows(self.event_id)
        with open(out,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(rows[0].keys() if rows else ["message"]); [w.writerow(list(r)) for r in rows]
        self.statusBar().showMessage("Report saved.")
    def settings_dialog(self):
        d=QDialog(self); d.setWindowTitle("OptiSys Settings"); f=QFormLayout(d); p=QLineEdit(self.settings.get("photoshop","")); l=QLineEdit(self.settings.get("lightroom","")); f.addRow("Photoshop",p); f.addRow("Lightroom",l); b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); b.accepted.connect(d.accept); b.rejected.connect(d.reject); f.addRow(b)
        if d.exec():self.settings.update(photoshop=p.text(),lightroom=l.text());self.save_settings()
    def closeEvent(self,e):self.db.close();e.accept()
if __name__=="__main__":
    app=QApplication(sys.argv);w=Main();w.show();sys.exit(app.exec())

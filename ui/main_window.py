from pathlib import Path
import csv,os
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QPixmap,QKeySequence,QAction
from PySide6.QtWidgets import *
from config import load_config,save_config,DB_FILE,VERSION
from core.database import Database
from core.scanner import discover,read_meta
from core.ingest import verified_copy
from core.adobe import launch,guess_apps
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"OptiSys v{VERSION}"); self.resize(1380,850); self.db=Database(DB_FILE); self.cfg=load_config(); self.event_id=None; self.rows=[]; self.build(); self.load_events()
    def build(self):
        root=QWidget(); self.setCentralWidget(root); main=QVBoxLayout(root)
        top=QHBoxLayout(); top.addWidget(QLabel(f"<b>OPTISYS</b>  <span style='color:#8994a5'>EVENT WORKFLOW // v{VERSION}</span>")); top.addStretch()
        self.event_box=QComboBox(); self.event_box.currentIndexChanged.connect(self.event_changed); top.addWidget(QLabel("EVENT")); top.addWidget(self.event_box)
        b=QPushButton("+ New Event"); b.clicked.connect(self.new_event); top.addWidget(b); main.addLayout(top)
        bar=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText("Search filename / camera / lens / path…"); self.search.textChanged.connect(self.refresh); bar.addWidget(self.search,2)
        self.filter=QComboBox(); self.filter.addItems(["All","RAW","JPEG","Rated","Rejected"]); self.filter.currentTextChanged.connect(self.refresh); bar.addWidget(self.filter)
        for text,fn in [("IMPORT FOLDER",self.import_folder),("EXPORT SELECTS",self.export_selects),("REPORT CSV",self.report)]: b=QPushButton(text); b.clicked.connect(fn); bar.addWidget(b)
        main.addLayout(bar)
        split=QSplitter(Qt.Horizontal); main.addWidget(split,1); left=QWidget(); ll=QVBoxLayout(left); self.list=QListWidget(); self.list.setIconSize(QSize(150,105)); self.list.currentItemChanged.connect(self.selected); ll.addWidget(self.list); self.progress=QProgressBar(); self.progress.setVisible(False); ll.addWidget(self.progress); split.addWidget(left)
        right=QWidget(); rl=QVBoxLayout(right); self.preview=QLabel("Select a photograph"); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(400,300); rl.addWidget(self.preview,2); self.info=QTextEdit(); self.info.setReadOnly(True); rl.addWidget(self.info,1)
        controls=QHBoxLayout()
        for text,fn in [("★ Rate",self.rate),("X Reject",self.reject),("↻ Clear",self.clear_flags),("Photoshop",self.photoshop),("Lightroom",self.lightroom),("Open Folder",self.open_folder)]: b=QPushButton(text); b.clicked.connect(fn); controls.addWidget(b)
        rl.addLayout(controls); split.addWidget(right); split.setSizes([650,650]); self.statusBar().showMessage("Ready"); self.shortcuts()
    def shortcuts(self):
        for seq,fn in [("1",lambda:self.set_rating(1)),("2",lambda:self.set_rating(2)),("3",lambda:self.set_rating(3)),("4",lambda:self.set_rating(4)),("5",lambda:self.set_rating(5)),("X",self.reject),("0",self.clear_flags)]:
            a=QAction(self); a.setShortcut(QKeySequence(seq)); a.triggered.connect(fn); self.addAction(a)
    def load_events(self):
        self.event_box.blockSignals(True); self.event_box.clear()
        for e in self.db.events(): self.event_box.addItem(e["name"],e["id"])
        self.event_box.blockSignals(False)
        if self.event_box.count(): self.event_box.setCurrentIndex(0); self.event_changed(0)
    def event_changed(self,_): self.event_id=self.event_box.currentData(); self.refresh()
    def new_event(self):
        name,ok=QInputDialog.getText(self,"New Event","Event name:")
        if not ok or not name.strip(): return
        client,_=QInputDialog.getText(self,"Client","Client name (optional):"); date,_=QInputDialog.getText(self,"Date","Date YYYY-MM-DD (optional):")
        e=self.db.create_event(name.strip(),client,date); self.load_events(); self.event_box.setCurrentText(e["name"])
    def import_folder(self):
        if not self.event_id: QMessageBox.warning(self,"OptiSys","Create/select an event first."); return
        folder=QFileDialog.getExistingDirectory(self,"Select card/folder to ingest",self.cfg.get("last_import") or str(Path.home()))
        if not folder:return
        self.cfg["last_import"]=folder; save_config(self.cfg); files=list(discover(folder))
        if not files: QMessageBox.information(self,"OptiSys","No supported image files found."); return
        self.progress.setVisible(True); self.progress.setRange(0,len(files)); self.progress.setValue(0); dup=errors=0; hashes=self.db.hashes(self.event_id)
        for i,p in enumerate(files,1):
            try:
                meta=read_meta(p)
                if meta.get("sha256") in hashes: dup+=1
                else: hashes.add(meta.get("sha256")); self.db.add_photo(self.event_id,meta)
            except Exception: errors+=1
            self.progress.setValue(i)
        self.progress.setVisible(False); self.refresh(); self.statusBar().showMessage(f"Imported {len(files)-dup-errors} | duplicates {dup} | errors {errors}")
    def refresh(self):
        self.list.clear()
        if not self.event_id:return
        self.rows=self.db.photos(self.event_id,self.search.text().strip(),self.filter.currentText().lower())
        for r in self.rows:
            star="★"*r["rating"] if r["rating"] else ""; flag="  [REJECT]" if r["rejected"] else ""; it=QListWidgetItem(f"{r['filename']}  {star}{flag}"); it.setData(Qt.UserRole,r["id"]); it.setToolTip(r["path"]); self.list.addItem(it)
    def current_row(self):
        it=self.list.currentItem()
        return next((r for r in self.rows if r["id"]==it.data(Qt.UserRole)),None) if it else None
    def selected(self,cur,_prev=None):
        r=self.current_row()
        if not r:return
        p=Path(r["path"])
        if p.suffix.lower() not in {".cr2",".cr3",".nef",".arw",".dng",".raf",".rw2",".orf",".srw",".pef",".raw"}:
            pix=QPixmap(str(p))
            if not pix.isNull(): self.preview.setPixmap(pix.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else:self.preview.setText("RAW file\n(embedded RAW preview module planned)")
        self.info.setPlainText("\n".join([f"FILE: {r['filename']}",f"PATH: {r['path']}",f"SIZE: {r['size']:,} bytes",f"SHA256: {r['sha256'] or '-'}",f"CAMERA: {r['camera'] or '-'}",f"LENS: {r['lens'] or '-'}",f"TAKEN: {r['taken_at'] or '-'}",f"ISO: {r['iso'] or '-'}",f"APERTURE: {r['aperture'] or '-'}",f"SHUTTER: {r['shutter'] or '-'}",f"RATING: {r['rating']}   REJECTED: {'YES' if r['rejected'] else 'NO'}",f"NOTE: {r['note'] or '-'}"]))
    def set_rating(self,n):
        r=self.current_row()
        if r:self.db.update_photo(r["id"],rating=n,rejected=0); self.refresh()
    def rate(self): self.set_rating(5)
    def reject(self):
        r=self.current_row()
        if r:self.db.update_photo(r["id"],rejected=1); self.refresh()
    def clear_flags(self):
        r=self.current_row()
        if r:self.db.update_photo(r["id"],rating=0,rejected=0); self.refresh()
    def adobe(self,key):
        r=self.current_row()
        if not r:return
        path=self.cfg.get(key) or guess_apps().get(key,"")
        if not path:path=QFileDialog.getOpenFileName(self,f"Select {key.title()} executable",filter="Executable (*.exe)")[0]
        if not path:return
        self.cfg[key]=path; save_config(self.cfg)
        try: launch(path,r["path"])
        except Exception as e: QMessageBox.warning(self,"Adobe launch",str(e))
    def photoshop(self): self.adobe("photoshop")
    def lightroom(self): self.adobe("lightroom")
    def open_folder(self):
        r=self.current_row()
        if r: os.startfile(str(Path(r["path"]).parent))
    def export_selects(self):
        if not self.event_id:return
        rated=[r for r in self.db.photos(self.event_id) if r["rating"]>0 and not r["rejected"]]
        if not rated: QMessageBox.information(self,"OptiSys","No rated, non-rejected photos."); return
        dest=QFileDialog.getExistingDirectory(self,"Export selects to")
        if not dest:return
        if Path(dest).resolve().drive.upper()=="C:": QMessageBox.warning(self,"OptiSys","C: is blocked for photo destinations."); return
        out=Path(dest)/"OptiSys_Selects"; out.mkdir(exist_ok=True); ok=0
        for r in rated:
            try: verified_copy(r["path"],out/Path(r["path"]).name); ok+=1
            except Exception: pass
        QMessageBox.information(self,"Export complete",f"Verified {ok}/{len(rated)} files into:\n{out}")
    def report(self):
        if not self.event_id:return
        path=QFileDialog.getSaveFileName(self,"Save CSV report","optisys_report.csv","CSV (*.csv)")[0]
        if not path:return
        rows=self.db.photos(self.event_id)
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(rows[0].keys() if rows else ["message"])
            for r in rows:w.writerow(list(r))
        self.statusBar().showMessage(f"Report saved: {path}")
    def closeEvent(self,e): self.db.close(); e.accept()

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap,QKeySequence,QAction
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QHBoxLayout,QPushButton
from pathlib import Path
class Viewer(QDialog):
    def __init__(self,main):
        super().__init__(main); self.main=main; self.setWindowTitle("OptiSys — Loupe"); self.showMaximized(); self.build()
    def build(self):
        self.setStyleSheet("QDialog{background:#050505;color:#ddd} QPushButton{background:#191919;color:#ddd;border:1px solid #333;padding:7px}")
        v=QVBoxLayout(self); self.img=QLabel(); self.img.setAlignment(Qt.AlignCenter); self.img.setStyleSheet("background:#050505"); v.addWidget(self.img,1)
        bar=QHBoxLayout(); self.caption=QLabel(); bar.addWidget(self.caption); bar.addStretch()
        for t,f in [("←",self.prev),("1",lambda:self.rate(1)),("2",lambda:self.rate(2)),("3",lambda:self.rate(3)),("4",lambda:self.rate(4)),("5",lambda:self.rate(5)),("X",self.main.reject),("→",self.next),("CLOSE",self.close)]: b=QPushButton(t); b.clicked.connect(f); bar.addWidget(b)
        v.addLayout(bar); self.show_row()
        for k,f in [("Left",self.prev),("Right",self.next),("1",lambda:self.rate(1)),("2",lambda:self.rate(2)),("3",lambda:self.rate(3)),("4",lambda:self.rate(4)),("5",lambda:self.rate(5)),("X",self.main.reject),("Escape",self.close)]:
            a=QAction(self); a.setShortcut(QKeySequence(k)); a.triggered.connect(f); self.addAction(a)
    def show_row(self):
        r=self.main.current
        if not r:return
        p=Path(r["path"])
        if p.exists() and p.suffix.lower() not in self.main.raw:
            pix=QPixmap(str(p)); self.img.setPixmap(pix.scaled(self.img.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else:self.img.setText("RAW preview is not decoded by the core viewer")
        self.caption.setText(r["filename"]+"   "+("★"*r["rating"] if r["rating"] else "UNRATED"))
    def resizeEvent(self,e): self.show_row(); super().resizeEvent(e)
    def next(self): self.main.next_photo(); self.show_row()
    def prev(self): self.main.prev_photo(); self.show_row()
    def rate(self,n): self.main.rate(n); self.show_row()

import os,sys,hashlib
from pathlib import Path
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QPixmap,QIcon,QKeySequence,QAction
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QListWidget,QListWidgetItem,QLabel,QPushButton,QLineEdit,QComboBox,QTextEdit,QMessageBox,QDialog,QAbstractItemView
from app import Main,Viewer,RAW

def professional_build(self):
    self.setWindowTitle("OptiSys — Darkroom")
    self.resize(1750,1050)
    self.setStyleSheet("""
    QMainWindow,QWidget{background:#171717;color:#d8d8d8;font-family:'Segoe UI';font-size:12px}
    QPushButton,QComboBox,QLineEdit{background:#262626;color:#ddd;border:1px solid #3b3b3b;border-radius:3px;padding:6px 9px}
    QPushButton:hover{background:#323232;border-color:#555}
    QLineEdit:focus,QComboBox:focus{border-color:#888}
    QListWidget{background:#111;border:0;outline:0}
    QListWidget::item{background:#191919;border:1px solid #292929;margin:3px;padding:2px}
    QListWidget::item:selected{background:#242424;border:2px solid #aaa}
    QTextEdit{background:#1b1b1b;color:#ccc;border:1px solid #2c2c2c}
    QStatusBar{background:#202020;color:#888}
    QSplitter::handle{background:#303030}
    """)
    root=QWidget();self.setCentralWidget(root);v=QVBoxLayout(root);v.setContentsMargins(7,5,7,5);v.setSpacing(5)
    head=QHBoxLayout()
    brand=QLabel("OPTISYS");brand.setStyleSheet("font-size:17px;font-weight:600;letter-spacing:3px;color:#eee")
    head.addWidget(brand);sub=QLabel("  DARKROOM / LIBRARY");sub.setStyleSheet("color:#777");head.addWidget(sub);head.addStretch()
    self.events=QComboBox();self.events.currentIndexChanged.connect(self.change_event);head.addWidget(self.events)
    b=QPushButton("+ EVENT");b.clicked.connect(self.new_event);head.addWidget(b);v.addLayout(head)
    bar=QHBoxLayout()
    self.search=QLineEdit();self.search.setPlaceholderText("Filter catalog…");self.search.textChanged.connect(self.refresh);bar.addWidget(self.search,3)
    self.mode=QComboBox();self.mode.addItems(["ALL","RAW","JPEG","RATED","REJECTED","UNRATED"]);self.mode.currentTextChanged.connect(self.refresh);bar.addWidget(self.mode)
    self.sort=QComboBox();self.sort.addItems(["taken","filename"]);self.sort.currentTextChanged.connect(self.refresh);bar.addWidget(self.sort)
    for text,fn in [("IMPORT",self.import_folder),("VERIFY",self.verify_event),("COMPARE",self.compare),("EXPORT",self.export),("BACKUP",self.backup),("REPORT",self.report)]:
        b=QPushButton(text);b.clicked.connect(fn);bar.addWidget(b)
    v.addLayout(bar)
    split=QSplitter(Qt.Horizontal);v.addWidget(split,1)
    left=QWidget();ll=QVBoxLayout(left);ll.setContentsMargins(0,0,0,0)
    self.grid=QListWidget();self.grid.setViewMode(QListWidget.IconMode);self.grid.setResizeMode(QListWidget.Adjust);self.grid.setMovement(QListWidget.Static);self.grid.setSelectionMode(QAbstractItemView.ExtendedSelection);self.grid.setIconSize(QSize(190,135));self.grid.setGridSize(QSize(210,172));self.grid.currentItemChanged.connect(self.select);self.grid.itemDoubleClicked.connect(lambda _:self.viewer());ll.addWidget(self.grid)
    split.addWidget(left)
    right=QWidget();rr=QVBoxLayout(right);rr.setContentsMargins(5,0,0,0)
    self.preview=QLabel("SELECT A PHOTO");self.preview.setAlignment(Qt.AlignCenter);self.preview.setStyleSheet("background:#0b0b0b;color:#555;font-size:11px");rr.addWidget(self.preview,5)
    self.info=QTextEdit();self.info.setReadOnly(True);self.info.setMaximumHeight(245);rr.addWidget(self.info)
    controls=QHBoxLayout()
    for text,fn in [("1",lambda:self.rate(1)),("2",lambda:self.rate(2)),("3",lambda:self.rate(3)),("4",lambda:self.rate(4)),("5",lambda:self.rate(5)),("P",self.pick),("X",self.reject),("0",self.clear),("LOUPE",self.viewer),("PHOTOSHOP",lambda:self.adobe("photoshop")),("LIGHTROOM",lambda:self.adobe("lightroom")),("FOLDER",self.folder)]:
        b=QPushButton(text);b.clicked.connect(fn);controls.addWidget(b)
    rr.addLayout(controls);split.addWidget(right);split.setSizes([1180,570])
    self.shortcuts();self.statusBar().showMessage("Ready  •  Local catalog  •  No cloud upload")

def fill_refresh(self):
    self.grid.clear();self.rows=[];self.current=None
    if not self.event_id:return
    self.rows=self.db.rows(self.event_id,self.search.text().strip(),self.mode.currentText(),self.sort.currentText())
    for r in self.rows:
        label=(("★"*r["rating"])+"  " if r["rating"] else "")+r["filename"]+("  ✕" if r["rejected"] else "")
        it=QListWidgetItem(label);it.setData(Qt.UserRole,r["id"]);it.setToolTip(r["path"])
        th=self.thumb(r["path"])
        if th:it.setIcon(QIcon(str(th)))
        self.grid.addItem(it)
    total=len(self.rows);rated=sum(r["rating"]>0 for r in self.rows);rej=sum(r["rejected"] for r in self.rows)
    self.statusBar().showMessage(f"{total:,} photos   •   {rated:,} rated   •   {rej:,} rejected")

Main.build=professional_build
Main.refresh=fill_refresh

if __name__=="__main__":
    app=QApplication(sys.argv)
    w=Main();w.show()
    sys.exit(app.exec())

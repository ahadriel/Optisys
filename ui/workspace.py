from PySide6.QtCore import Qt,QSize,Signal
from PySide6.QtGui import QPixmap,QIcon,QKeySequence,QAction
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QLineEdit,QComboBox,QListWidget,QListWidgetItem,QSplitter,QScrollArea,QFrame,QTextEdit,QSlider
from pathlib import Path
from PIL import Image,ImageOps
import hashlib

class PhotoGrid(QListWidget):
    photoActivated=Signal(object)
    def __init__(self):
        super().__init__(); self.setViewMode(QListWidget.IconMode); self.setResizeMode(QListWidget.Adjust); self.setMovement(QListWidget.Static); self.setSpacing(6); self.setUniformItemSizes(True); self.setIconSize(QSize(190,135)); self.setGridSize(QSize(210,175)); self.setSelectionMode(QListWidget.ExtendedSelection)
    def add_photo(self,row,thumb):
        text=row["filename"]
        if row["rating"]: text="★"*row["rating"]+"  "+text
        if row["rejected"]: text="✕  "+text
        it=QListWidgetItem(QIcon(str(thumb)) if thumb else QIcon(),text); it.setData(Qt.UserRole,row["id"]); it.setToolTip(row["path"]); self.addItem(it)

class Filmstrip(QListWidget):
    def __init__(self):
        super().__init__(); self.setViewMode(QListWidget.IconMode); self.setResizeMode(QListWidget.Adjust); self.setMovement(QListWidget.Static); self.setIconSize(QSize(110,75)); self.setGridSize(QSize(125,105)); self.setFixedHeight(125)

class Workspace(QWidget):
    def __init__(self,main):
        super().__init__(); self.main=main; self.full=False; self.build()
    def build(self):
        root=QVBoxLayout(self); root.setContentsMargins(8,6,8,6); root.setSpacing(6)
        top=QHBoxLayout(); brand=QLabel("OPTISYS"); brand.setObjectName("brand"); top.addWidget(brand); top.addWidget(QLabel("  LIBRARY")); top.addStretch()
        for t,f in [("IMPORT",self.main.import_folder),("VERIFY",self.main.verify_event),("EXPORT",self.main.export),("REPORT",self.main.report)]: b=QPushButton(t); b.clicked.connect(f); top.addWidget(b)
        root.addLayout(top)
        tools=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText("Filter photos…"); self.search.textChanged.connect(self.main.refresh); tools.addWidget(self.search,3)
        self.mode=QComboBox(); self.mode.addItems(["ALL","RAW","JPEG","RATED","REJECTED","UNRATED"]); self.mode.currentTextChanged.connect(self.main.refresh); tools.addWidget(self.mode)
        self.sort=QComboBox(); self.sort.addItems(["taken","filename"]); self.sort.currentTextChanged.connect(self.main.refresh); tools.addWidget(self.sort); root.addLayout(tools)
        split=QSplitter(Qt.Horizontal); root.addWidget(split,1)
        left=QFrame(); left.setObjectName("panel"); ll=QVBoxLayout(left); lab=QLabel("CATALOG"); lab.setObjectName("section"); ll.addWidget(lab); self.grid=PhotoGrid(); self.grid.currentItemChanged.connect(self.main.select); self.grid.itemDoubleClicked.connect(lambda _:self.main.viewer()); ll.addWidget(self.grid); split.addWidget(left)
        right=QFrame(); right.setObjectName("panel"); rv=QVBoxLayout(right)
        self.preview=QLabel("SELECT A PHOTO"); self.preview.setAlignment(Qt.AlignCenter); self.preview.setStyleSheet("background:#0b0b0b;color:#555;"); rv.addWidget(self.preview,5)
        self.info=QTextEdit(); self.info.setReadOnly(True); self.info.setMaximumHeight(210); rv.addWidget(self.info)
        ctl=QHBoxLayout()
        for t,f in [("1",lambda:self.main.rate(1)),("2",lambda:self.main.rate(2)),("3",lambda:self.main.rate(3)),("4",lambda:self.main.rate(4)),("5",lambda:self.main.rate(5)),("REJECT",self.main.reject),("CLEAR",self.main.clear),("VIEW",self.main.viewer),("PS",lambda:self.main.adobe("photoshop")),("LR",lambda:self.main.adobe("lightroom"))]: b=QPushButton(t); b.clicked.connect(f); ctl.addWidget(b)
        rv.addLayout(ctl); split.addWidget(right); split.setSizes([900,550])
        self.film=Filmstrip(); root.addWidget(self.film)
    def fill(self,rows):
        self.grid.clear(); self.film.clear()
        for r in rows:
            th=self.main.thumb(r["path"])
            self.grid.add_photo(r,th)
            if th:
                it=QListWidgetItem(QIcon(str(th)),r["filename"]); it.setData(Qt.UserRole,r["id"]); self.film.addItem(it)

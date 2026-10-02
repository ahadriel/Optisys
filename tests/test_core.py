import tempfile
from pathlib import Path
from core.database import Database
from core.scanner import sha256_file
def test_database_event():
    with tempfile.TemporaryDirectory() as d:
        db=Database(Path(d)/"test.sqlite3"); e=db.create_event("Demo"); assert e["name"]=="Demo"; db.close()
def test_hash():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"x.txt"; p.write_text("optisys"); assert len(sha256_file(p))==64

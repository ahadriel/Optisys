# OptiSys v20.0
## Professional Event Photography Workflow System

OptiSys is a local-first Windows desktop workflow for event photographers. It catalogs photographs without uploading client media, verifies ingest copies, reads metadata, supports culling/rating, and provides fast hand-off to Adobe apps.

### v20.0 build goals
- Local SQLite catalog
- Recursive ingest and verified copying
- SHA-256 duplicate detection
- RAW/JPEG/PNG/TIFF/WEBP awareness
- EXIF metadata extraction when available
- Thumbnail-aware review
- Search and filters
- Ratings, flags and notes
- Batch export of selected photos
- Event folder creation
- Adobe Photoshop / Lightroom executable settings
- Keyboard-first culling
- CSV report export
- No cloud dependency
- C: destination guard for photo copies

### Run
1. Install Python 3.11+.
2. Open CMD in this repository.
3. Run `python -m venv .venv`
4. Run `.venv\\Scripts\\activate`
5. Run `pip install -r requirements.txt`
6. Run `python app.py`

Or run `run_optisys.bat`.

OptiSys does not claim ownership of photographs or user data. See LICENSE.

from pathlib import Path
import os
BASE_DIR=Path(__file__).resolve().parents[2]
STORAGE=Path(os.getenv('ORIGON_STORAGE', BASE_DIR/'storage')).resolve()
DB_PATH=STORAGE/'database'/'origon.db'
for name in ('database','media','music','voice','compositions','renders','exports','backups','trash','products','batches'):
    (STORAGE/name).mkdir(parents=True, exist_ok=True)

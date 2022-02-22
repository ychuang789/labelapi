from pathlib import Path, PurePath

ROOT_DIR = PurePath(__file__).parent
LOGS_DIR = Path(ROOT_DIR / "logs")
Path(LOGS_DIR).mkdir(exist_ok=True)

SCRAP_FOLDER = Path(ROOT_DIR / "scrap_file")
Path(SCRAP_FOLDER).mkdir(exist_ok=True)

SAVE_FOLDER = Path(ROOT_DIR / "save_file")
Path(SAVE_FOLDER).mkdir(exist_ok=True)

RULE_FOLDER = Path(ROOT_DIR / "rules")
Path(RULE_FOLDER).mkdir(exist_ok=True)

MODEL_IMPORT_FOLDER = Path(ROOT_DIR / "upload_files")
Path(MODEL_IMPORT_FOLDER).mkdir(exist_ok=True)

SAVE_DETAIL_FOLDER = Path(ROOT_DIR / "save_detail_folder")
Path(SAVE_DETAIL_FOLDER).mkdir(exist_ok=True)

SAVE_TW_FOLDER = Path(ROOT_DIR / "save_term_weight_folder")
Path(SAVE_TW_FOLDER).mkdir(exist_ok=True)

# only use this in lab machine
AUDIENCE_PRODUCTION_PATH = '/home/deeprd2/audience_production'

DEEPNLP_POS_API = "http://127.0.0.1/segment"
DEEPNLP_POS_API_TOKEN = ""

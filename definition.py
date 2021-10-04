from pathlib import Path, PurePath

ROOT_DIR = PurePath(__file__).parent
ROOT_LOG_DIR = Path(ROOT_DIR / "logs")


DEEPNLP_POS_API = "http://127.0.0.1/segment"
DEEPNLP_POS_API_TOKEN = ""

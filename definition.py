from pathlib import Path, PurePath

# dir
ROOT_DIR = PurePath(__file__).parent
LOGS_DIR = Path(ROOT_DIR / "logs")
Path(LOGS_DIR).mkdir(exist_ok=True)
SCRAP_FOLDER = Path(ROOT_DIR / "scrap_file")
Path(SCRAP_FOLDER).mkdir(exist_ok=True)

# configuration
DEFAULT_CONFIG = Path(ROOT_DIR / "system_config.yaml")

# deepnlp tokenizer
DEEPNLP_POS_API = "http://127.0.0.1/segment"
DEEPNLP_POS_API_TOKEN = ""

# sql
LIM = 1000
GET_DATA_QUERY = f"SELECT id, s_area_id, author, title, content, post_time FROM ts_page_content LIMIT {LIM}"

from pathlib import Path, PurePath

# dir
ROOT_DIR = PurePath(__file__).parent

LOGS_DIR = Path(ROOT_DIR / "logs")
Path(LOGS_DIR).mkdir(exist_ok=True)

SCRAP_FOLDER = Path(ROOT_DIR / "scrap_file")
Path(SCRAP_FOLDER).mkdir(exist_ok=True)

# sql
LIM = 1000
GET_DATA_QUERY = f"SELECT id, s_area_id, author, title, content, post_time FROM ts_page_content LIMIT {LIM}"

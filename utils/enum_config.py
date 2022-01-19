from enum import Enum
from pathlib import Path

from definition import RULE_FOLDER

INPUT_TABLE = "predicting_jobs_predictingresult"
INPUT_COLUMNS = "source_author, applied_content, created_at"

class NATag(Enum):
    na_tag = '一般'

class PredictTaskStatus(Enum):
    SUCCESS = 'SUCCESS'
    PENDING = 'PENDING'
    FAILURE = 'FAILURE'
    BREAK = 'BREAK'
    PROD_SUCCESS = 'finish'
    PROD_NODATA = 'no_data'

class ModelTaskStatus(Enum):
    PENDING = 'pending'
    STARTED = 'started'
    FINISHED = 'finished'
    FAILED = 'failed'
    BREAK = 'break'
    UNTRAINABLE = 'untrainable'

class DatasetType(Enum):
    TRAIN = 'train'
    DEV = 'dev'
    TEST = 'test'
    EXT_TEST = 'ext_test'

class TWFeatureModel(Enum):
    SGD = 'sgd'

class ModelType(Enum):
    KEYWORD_MODEL = "keyword_model"
    REGEX_MODEL = "regex_model"
    RANDOM_FOREST_MODEL = "random_forest_model"
    TERM_WEIGHT_MODEL = "term_weight_model"

class PredictTarget(Enum):
    AUTHOR = "author"
    CONTENT = "content"
    S_AREA_ID = "s_area_id"
    TITLE = "title"

class RulesTarget:
    AUTHOR_NAME_KEYWORD = Path(RULE_FOLDER / "author_name.pkl")

class KeywordMatchType:
    PARTIALLY = "partially"
    ABSOLUTELY = "absolutely"
    START = "start"
    END = "end"

class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predicting target type."

# class SampleResultTable(str, Enum):
#     blog = 'wh_panel_mapping_blog'
#     Comment = 'wh_panel_mapping_Comment'
#     Dcard = 'wh_panel_mapping_Dcard'
#     fbfans = 'wh_panel_mapping_fbfans'
#     fbgroup = 'wh_panel_mapping_fbgroup'
#     fbkol = 'wh_panel_mapping_fbkol'
#     fbpm = 'wh_panel_mapping_fbpm'
#     fbprivategroup = 'wh_panel_mapping_fbprivategroup'
#     forum = 'wh_panel_mapping_forum'
#     Instagram = 'wh_panel_mapping_Instagram'
#     news = 'wh_panel_mapping_news'
#     plurk = 'wh_panel_mapping_plurk'
#     Ptt = 'wh_panel_mapping_Ptt'
#     Tiktok = 'wh_panel_mapping_Tiktok'
#     Twitter = 'wh_panel_mapping_Twitter'
#     video = 'wh_panel_mapping_video'
#     Youtube = 'wh_panel_mapping_Youtube'
#
# class Label(str, Enum):
#     male = '男性'
#     female = '女性'
#     unmarried = '未婚'
#     married = '已婚'
#     child = '孩子'
#     parenting = '有子女'
#     young = '青年'
#     employee = '上班族'
#     student = '學生'




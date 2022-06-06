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

class RuleType(Enum):
    KEYWORD = "keyword"
    REGEX = "regex"
    TERM_WEIGHT = "term_weight"

class MatchType(Enum):
    START = 'start'
    END = 'end'
    EXACTLY = 'exactly'
    PARTIALLY = 'partially'

class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predicting target type."

class RulesTarget:
    AUTHOR_NAME_KEYWORD = Path(RULE_FOLDER / "author_name.pkl")

# Todo: 修改 abs -> exactly，對應站台
class KeywordMatchType:
    PARTIALLY = "partially"
    EXACTLY = 'exactly'
    START = "start"
    END = "end"






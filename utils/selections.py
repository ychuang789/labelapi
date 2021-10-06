
from enum import  Enum

INPUT_TABLE = "predicting_jobs_predictingresult"
INPUT_COLUMNS = "source_author, applied_content, created_at"


class ModelType(Enum):
    RULE_MODEL = "rule_model"
    KEYWORD_MODEL = "keyword_model"


class PredictTarget:
    CONTENT = "content"
    AUTHOR_NAME = "author_name"
    S_AREA_ID = "s_area_id"


class KeywordMatchType:
    PARTIALLY = "partially"
    ABSOLUTELY = "absolutely"
    START = "start"
    END = "end"

class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predict target type."


class QueryStatements(Enum):
    # QUERY_FEMALE = f'SELECT {INPUT_COLUMNS} FROM {INPUT_TABLE} WHERE label_name LIKE "女%" AND applied_feature="author"'
    # QUERY_MALE = f'SELECT {INPUT_COLUMNS} FROM {INPUT_TABLE} WHERE label_name LIKE "男%" AND applied_feature="author"'
    # MALE_RULE = f'SELECT * FROM male_author_name_rules'
    # FEMALE_RULE = f'SELECT * FROM female_author_name_rules'
    QUERY = f'SELECT * FROM {INPUT_TABLE} WHERE applied_feature="author"'


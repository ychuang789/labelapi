from enum import Enum



class ModelType(Enum):
    RULE_MODEL = "rule_model"
    KEYWORD_MODEL = "keyword_model"

class PredictTarget(Enum):
    CONTENT = "content"
    AUTHOR_NAME = "author_name"
    S_AREA_ID = "s_area_id"

class KeywordMatchType(Enum):
    PARTIALLY = "partially"
    ABSOLUTELY = "absolutely"
    START = "start"
    END = "end"

class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predict target type."


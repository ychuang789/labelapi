from datetime import datetime
from pydantic import BaseModel


class PreprocessTaskDelete(BaseModel):
    TASK_ID: int


class PreprocessTaskUpdate(BaseModel):
    LABEL: str
    FEATURE: str = "CONTENT"
    MODEL_NAME: str = "REGEX_MODEL"
    CREATE_TIME: datetime = datetime.now()

from datetime import datetime
from pydantic import BaseModel


class PreprocessTaskCreate(BaseModel):
    NAME: str
    FEATURE: str
    MODEL_NAME: str
    CREATE_TIME: datetime = datetime.now()


class PreprocessTaskDelete(BaseModel):
    TASK_ID: int


class PreprocessTaskUpdate(BaseModel):
    NAME: str
    FEATURE: str
    MODEL_NAME: str
    CREATE_TIME: datetime = datetime.now()

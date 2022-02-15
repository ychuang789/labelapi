import os
from datetime import date
from pydantic import BaseModel
from typing import Dict, Optional, List

from settings import DatabaseConfig


class TaskConfig(BaseModel):
    START_TIME: date = "2020-01-01"
    END_TIME: date = "2021-01-01"
    INPUT_SCHEMA: str = os.getenv("INPUT_SCHEMA")
    INPUT_TABLE: str = os.getenv("INPUT_TABLE")
    COUNTDOWN: int = 5
    QUEUE: str = "queue1"
    MODEL_ID_LIST: List[str] = None
    SITE_CONFIG: Optional[Dict] = None


class AbortConfig(BaseModel):
    TASK_ID: str = 'string'


class DeleteConfig(BaseModel):
    TASK_ID: str = None


class DumpConfig(BaseModel):
    ID_LIST: List[int] = "place task_id list or predicting_job_id list here"
    OLD_TABLE_DATABASE: str = DatabaseConfig.DUMP_FROM_SCHEMA
    NEW_TABLE_DATABASE: str = DatabaseConfig.OUTPUT_SCHEMA
    DUMP_DATABASE: str = DatabaseConfig.DUMP_TO_SCHEMA
    QUEUE: str = "queue1"


class TaskSampleResult:
    OUTPUT_SCHEMA: str = os.getenv('OUTPUT_SCHEMA')
    ORDER_COLUMN: str = 'create_time'
    NUMBER: int = 50
    OFFSET: int = 1000



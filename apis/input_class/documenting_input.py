from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from utils.enum_config import DocumentDatasetType, DocumentTaskType, DocumentRulesType, DocumentMatchType


class DocumentRequest(BaseModel):
    NAME: Optional[str] = None
    DESCRIPTION: Optional[str] = None
    TASK_TYPE: Optional[DocumentTaskType] = None
    IS_MULTI_LABEL: Optional[str] = False

    class Config:
        use_enum_values = True


class DatasetRequest(BaseModel):
    TITLE: Optional[str] = ""
    AUTHOR: Optional[str] = ""
    S_ID: Optional[str] = ""
    S_AREA_ID: Optional[str] = ""
    CONTENT: Optional[str] = "add some text data here"
    POST_TIME: Optional[datetime] = None
    # LABEL: Optional[str] = "assign the label here"
    DATASET_TYPE: Optional[DocumentDatasetType] = DocumentDatasetType.TRAIN

    class Config:
        use_enum_values = True


class RulesRequest(BaseModel):
    CONTENT: Optional[str] = "add a rule"
    LABEL: Optional[str] = "assign the label here"
    RULE_TYPE: Optional[DocumentRulesType] = DocumentRulesType.REGEX
    MATCH_TYPE: Optional[DocumentMatchType] = DocumentMatchType.PARTIALLY

    class Config:
        use_enum_values = True

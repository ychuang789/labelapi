from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator

from utils.enum_config import DocumentDatasetType, DocumentTaskType, DocumentRulesType, DocumentMatchType


class DocumentRequest(BaseModel):
    NAME: Optional[str] = None
    DESCRIPTION: Optional[str] = None
    TASK_TYPE: Optional[DocumentTaskType] = DocumentTaskType.RULE
    IS_MULTI_LABEL: DocumentTaskType[bool] = False


class DatasetRequest(BaseModel):
    TITLE: str = None
    AUTHOR: str = None
    S_ID: str = None
    S_AREA_ID: str = None
    CONTENT: str = "add some text data here"
    POST_TIME: datetime = None
    LABEL: str = "assign the label here"
    DOCUMENT_TYPE: DocumentDatasetType = DocumentDatasetType.TRAIN


class RulesRequest(BaseModel):
    CONTENT: str = "add a rule"
    LABEL: str = "assign the label here"
    RULE_TYPE: DocumentRulesType = DocumentRulesType.REGEX
    MATCH_TYPE: DocumentMatchType = DocumentMatchType.PARTIALLY


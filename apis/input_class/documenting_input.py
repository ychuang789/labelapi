from pydantic import BaseModel, validator

from utils.enum_config import DocumentType


class DocumentAddRequest(BaseModel):
    NAME: str = None
    DESCRIPTION: str = None
    TASK_TYPE: DocumentType = DocumentType.TRAIN
    IS_MULTI_LABEL: bool = False



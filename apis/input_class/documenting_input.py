from pydantic import BaseModel, validator

from utils.enum_config import DocumentType


class DocumentRequest(BaseModel):
    NAME: str = None
    DESCRIPTION: str = None
    IS_MULTI_LABEL: bool = False

class DatasetRequest(BaseModel):
    pass



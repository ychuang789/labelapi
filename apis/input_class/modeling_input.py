from pydantic import BaseModel
from typing import Dict, Union

from settings import LABEL
from utils.enum_config import ModelType, PredictTarget


class ModelingTrainingConfig(BaseModel):
    # TRAINING_SCHEMA: str = os.getenv('TRAINING_SCHEMA')
    QUEUE: str = "queue2"
    DATASET_DB: str = 'audience-toolkit-django'
    DATASET_NO: int = 1
    TASK_ID: str = None
    PREDICT_TYPE: str = PredictTarget.CONTENT.name
    MODEL_TYPE: str = ModelType.RANDOM_FOREST_MODEL.name
    MODEL_INFO: Dict[str, Union[str, Dict]] = {"model_path": "model_path",
                                               "feature_model": "SGD"
                                               }


class ModelingTestingConfig(BaseModel):
    QUEUE: str = "queue2"
    DATASET_DB: str = 'audience-toolkit-django'
    DATASET_NO: int = 1
    TASK_ID: str = None
    PREDICT_TYPE: str = PredictTarget.CONTENT.name
    MODEL_TYPE: str = ModelType.RANDOM_FOREST_MODEL.name
    MODEL_INFO: Dict[str, Union[str, Dict]] = {"model_path": "model_path"}


class ModelingAbort(BaseModel):
    TASK_ID: str = None


class ModelingDelete(BaseModel):
    TASK_ID: str = None


class ModelingUpload(BaseModel):
    QUEUE: str = "queue2"
    TASK_ID: str = None
    UPLOAD_JOB_ID: int = None
    PREDICT_TYPE: str = PredictTarget.CONTENT.name
    MODEL_PATH: str = None


class TermWeightsAdd(BaseModel):
    TASK_ID: str
    LABEL: str
    TERM: str
    WEIGHT: float


class TermWeightsUpdate(BaseModel):
    TERM_WEIGHT_ID: int
    LABEL: str
    TERM: str
    WEIGHT: float


class TermWeightsDelete(BaseModel):
    TERM_WEIGHT_ID: int

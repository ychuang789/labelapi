
from celery import Celery

from settings import CeleryConfig
from utils.helper import get_logger
from utils.run_label_task import labeling

name = CeleryConfig.name
celery_app = Celery(name=name,
                    backend=CeleryConfig.backend,
                    broker=CeleryConfig.broker)

celery_app.conf.update(enable_utc=CeleryConfig.enable_utc)
celery_app.conf.update(timezone=CeleryConfig.timezone)
celery_app.conf.update(result_extended=True)

@celery_app.task(name=f'{name}.label_data', track_started=True)
def label_data(pattern_path, model_type, predict_type):
    _logger = get_logger('label_data')
    return labeling(model_type, predict_type, pattern_path, _logger)

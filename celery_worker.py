from celery import Celery

from settings import CeleryConfig

name = CeleryConfig.name

celery = Celery(name=name,
                backend=CeleryConfig.backend,
                broker=CeleryConfig.broker)

celery.conf.update(enable_utc=CeleryConfig.enable_utc)
celery.conf.update(timezone=CeleryConfig.timezone)
celery.conf.update(result_extended=True)

@celery.task(name=f'{name}.scrap_data', track_started=True)
def scrap_data():


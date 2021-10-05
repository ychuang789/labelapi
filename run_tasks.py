import click

from celery_worker import label_data
from utils.helper import get_logger


@click.command()
@click.option('--pattern_file_path', prompt='please input your pattern rule here')
@click.option('--model_type', type=click.Choice(['rule_model','keyword_model'], case_sensitive=False),
              prompt='please input your model_type here')
@click.option('--predict_type', type=click.Choice(['content','author_name', 's_area_id'], case_sensitive=False),
              prompt='please input your predict_type here')
def put_task(pattern_file_path, model_type, predict_type):
    _logger = get_logger('scrap_data')

    try:
        result = label_data.apply_async((pattern_file_path, model_type, predict_type))
        _logger.info('==========')
        _logger.info(f"Task init ...")
        _logger.info(f"*** Task id ***")
        _logger.info(f"{result.id}")
        _logger.info(f"*** Task status ***")
        _logger.info(f"{result.status}")

    except:
        _logger.error('Cannot put the task, see logging')

if __name__ == '__main__':
    put_task()



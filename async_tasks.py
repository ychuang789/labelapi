import click
from celery.result import AsyncResult
from celery_worker import label_data
from utils.helper import get_logger

_logger = get_logger('get_task')

@click.command()
@click.option('--task_id', prompt='input the task id')
@click.option('--task_type', prompt='input the task type',
              type=click.Choice(['get', 'revoke'], case_sensitive=False))
def async_get(task_id, task_type):
    _logger.info('===========')
    _logger.info(f'Task id: {task_id}')
    _logger.info(f'Task type: {task_type}')

    if task_type == 'get':
        result = AsyncResult(task_id, app=label_data)
        _logger.info(f'The task status is {result.status}')

        if result.status == 'SUCCESS':
            print(result.get().head())


    if task_type == 'revoke':
        result = AsyncResult(task_id)
        _logger.info(f'The task status is {result.status}')
        try:
            result.revoke(terminate=True)
            _logger.info(f'revoke the task {task_id}')
        except:
            _logger.error(f'cannot revoke the task {task_id}')

if __name__ == '__main__':
    async_get()



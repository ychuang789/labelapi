from datetime import datetime
from memory_profiler import memory_usage

from utils.helper import get_logger

_logger = get_logger('label_data')

def memory_usage_tracking(method):
    def measure_task(*args, **kwargs):
        start_time_of_task = datetime.now()
        mem_usage, result = memory_usage(
            (method, args, kwargs), retval=True, max_usage=True)
        result = method(*args, **kwargs)
        end_time_of_task = datetime.now()

        _logger.info(
            f'{method.__name__} completed in '
            f'{(end_time_of_task - start_time_of_task).total_seconds()/60} minutes '
            f'with max mem: {mem_usage[0]} MB')

        return result

    return measure_task

from datetime import datetime

import pandas as pd
import psutil
from memory_profiler import memory_usage

from settings import DatabaseInfo
from utils.database_core import update_memory_time_to_state
from utils.helper import get_logger

_logger = get_logger('measure')


def memory_usage_tracking(method):
    def measure_task(*args, **kwargs):
        start_time_of_task = datetime.now()
        _logger.info(f'start tracking memory info at {start_time_of_task} ')
        mem_usage, result = memory_usage(
            (method, args, kwargs), retval=True, max_usage=True)
        # result = method(*args, **kwargs)
        end_time_of_task = datetime.now()

        _logger.info(f'completed in {(end_time_of_task - start_time_of_task).total_seconds()/60} minutes with max mem: {mem_usage} MB')

        run_time = (end_time_of_task - start_time_of_task).total_seconds()/60

        # update_memory_time_to_state(result.id, run_time, round(mem_usage), _logger, schema=DatabaseInfo.output_schema)

        result.update({'memory_usage': [run_time, mem_usage]})
        return result

    return measure_task


def track_cpu_usage():
    """
    track the cpu info
    """
    cpu_dict = { "cpu_percent" : psutil.cpu_percent(interval=None, percpu=True),
                 "cpu_freq": psutil.cpu_freq(),
                 "cpu_load_avg": [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]}

    return cpu_dict




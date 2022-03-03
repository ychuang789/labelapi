from typing import List

from utils.data.input_example import InputExample
from workers.preprocessing.data_filter_core import DataFilterWorker


class DataFilterBuilder:

    @staticmethod
    def get_task_instance(id_list: List[int]):
        return [DataFilterWorker(filter_task_id=i) for i in id_list]

    @staticmethod
    def method_chain(start: List[InputExample], ins_list: List[DataFilterWorker]):
        temp_result = start
        for ins in ins_list:
            if not hasattr(ins, 'run_task'):
                raise ValueError('Instance should contain run_task method')
            temp_result = ins.run_task(temp_result)
        return temp_result

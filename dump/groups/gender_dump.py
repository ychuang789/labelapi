from collections import defaultdict
from typing import List, Dict

from dump.groups.dump_helper import ResultMissingError, TaskUnfinishedError
from dump.groups.groups_interface import IGroups
from dump.utils.check_merge_2020 import get_generate_dict_from_state
from settings import TABLE_GROUPS_FOR_INDEX



class Gender_Dump(IGroups):
    def __init__(self, task_ids: List[str], input_database: str,
                 output_database: str):
        super().__init__(task_ids=task_ids, input_database=input_database,
                         output_database=output_database, generate_dict=defaultdict(list),
                         logger_name='gender_dump')
        self.get_generate_dict()


    def get_generate_dict(self):
        state_list = get_generate_dict_from_state(self.task_ids)
        _state_checker(state_list)

        for item_dict in state_list:
            for result_table, source_group in TABLE_GROUPS_FOR_INDEX.items():
                if ',' in item_dict.get('result'):
                    if item_dict.get('result').split(',')[0] in source_group:
                        self.generate_dict[result_table].append(item_dict.get('task_id'))
                else:
                    if item_dict.get('result') in source_group:
                        self.generate_dict[result_table].append(item_dict.get('task_id'))
    # def run_merge(self):







def _state_checker(state_list: List[Dict]) -> None:
    for i in state_list:
        if i.get('prod_stat') != 'finish':
            raise TaskUnfinishedError(f"task {i.get('task_id')} is unfinished")



from collections import defaultdict
from typing import List, Dict

from dump.groups.dump_helper import TaskUnfinishedError
from dump.groups.groups_interface import IGroups
from dump.utils.check_merge_2020 import get_generate_dict_from_state
from dump.utils.dump_core import run, execute_zip_command
from settings import TABLE_GROUPS_FOR_INDEX, TABLE_PREFIX


class GenderDump(IGroups):
    def __init__(self, task_ids: List[str], input_database: str,
                 output_database: str):
        super().__init__(task_ids=task_ids, input_database=input_database,
                         output_database=output_database, generate_dict=defaultdict(list),
                         result_table_dict=defaultdict(list),
                         logger_name='gender_dump', prefix=TABLE_PREFIX, conflict_term='GENDER')

        self.logger.info(f'start initializing {self.conflict_term.lower()} dumping workflow...')
        self.get_generate_dict()

    def get_generate_dict(self):
        state_list = get_generate_dict_from_state(self.task_ids)
        _state_checker(state_list)

        for item_dict in state_list:
            if ',' in item_dict.get('result'):
                for i in item_dict.get('result').split(','):
                    table_name = self.prefix + i
                    self.result_table_dict[item_dict.get('task_id')].append(table_name)
            else:
                table_name = self.prefix + item_dict.get('result')
                self.result_table_dict[item_dict.get('task_id')].append(table_name)

        for item_dict in state_list:
            for result_table, source_group in TABLE_GROUPS_FOR_INDEX.items():
                if ',' in item_dict.get('result'):
                    if item_dict.get('result').split(',')[0] in source_group:
                        self.generate_dict[result_table].append(item_dict.get('task_id'))
                else:
                    if item_dict.get('result') in source_group:
                        self.generate_dict[result_table].append(item_dict.get('task_id'))

    def run_merge(self):
        self.logger.info(f'start executing merging...')
        run(self.generate_dict, self.result_table_dict, self.input_database,
            self.output_database, self.prefix,
            self.conflict_term, self.logger)

    # run run_merge first
    def dump_zip(self):
        for key in self.generate_dict.keys():
            table_name = self.prefix + key + '_dump'

            self.logger.info(f'start dumping {table_name} to zip...')
            execute_zip_command(table_name)


def _state_checker(state_list: List[Dict]) -> None:
    for i in state_list:
        if i.get('prod_stat') != 'finish':
            raise TaskUnfinishedError(f"task {i.get('task_id')} is unfinished")



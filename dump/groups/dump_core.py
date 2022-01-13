from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Union

import pandas as pd
from tqdm import tqdm

from dump.groups.groups_interface import DumpInterface
from dump.utils.dump_helper import execute_zip_command, truncate_table, get_current_data, get_old_table_list, \
    get_table_suffix_condition, get_old_data, merge_data, create_new_table, write_into_table, clean_rest, \
    get_generate_dict_from_state, get_dump_table_list, get_dump_table_ids
from settings import TABLE_GROUPS_FOR_INDEX, TABLE_PREFIX, DUMP_COLUMNS, SITE_SCHEMA
from utils.exception_tool.exception_manager import TaskUnfinishedError


class DumpWorker(DumpInterface):
    def __init__(self, id_list: Union[List[str], List[int]], old_table_database: str,
                 new_table_database: str, dump_database: str, verbose: bool = False):
        super().__init__(id_list=id_list, old_table_database=old_table_database,
                         new_table_database=new_table_database, dump_database=dump_database,
                         generate_dict=defaultdict(list), result_table_dict=defaultdict(list),
                         logger_name='dump', verbose=verbose, prefix=TABLE_PREFIX)

        self.logger.info(f'start initializing dumping workflow...')
        self.get_generate_dict()

    def __str__(self):
        return f"result_table_dict: {self.result_table_dict}\ngenerate_dict: {self.generate_dict}"

    def run_merge(self):
        self.logger.info(f'start executing merging...')
        self.logger.debug(f'clean up old data')
        self.clean_up_table()
        self.execute()
        return [self.prefix + k for k in self.generate_dict.keys()]

    def get_generate_dict(self):

        if isinstance(self.id_list[0], int):
            task_ids = [v for item in self.get_site_ids() for v in item.values()]
        elif isinstance(self.id_list[0], str):
            task_ids = self.id_list
        else:
            raise TypeError(f"expect id list input as list integer or list string, "
                            f"but get {type(self.id_list[0])} instead")

        state_list = get_generate_dict_from_state(task_ids)
        state_checker(state_list)

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

        self.logger.debug(f'{self.result_table_dict}')
        self.logger.debug(f'{self.generate_dict}')

    def get_site_ids(self):
        return get_dump_table_ids(schema=SITE_SCHEMA, condition=self.id_list)

    def dump_zip(self):
        for key in self.generate_dict.keys():
            table_name = self.prefix + key

            self.logger.info(f'start dumping {table_name} to zip...')
            execute_zip_command(table_name)

    def clean_up_table(self):
        if table_list := [v for item in get_dump_table_list(schema=self.dump_database) for v in item.values()]:
            for tb in table_list:
                truncate_table(table_name=tb, schema=self.dump_database)

    def execute(self, now: datetime = datetime.now()):
        for table_name, task_ids in tqdm(self.generate_dict.items()):
            self.logger.info(f'start generating {table_name} dumping flow...')
            self.logger.info(f'start scraping result data...')
            new_df = pd.DataFrame(columns=DUMP_COLUMNS)
            for task_id in task_ids:
                for result_table in self.result_table_dict.get(task_id):
                    current_df = get_current_data(self.new_table_database, result_table, task_id)
                    new_df = new_df.append(current_df)

            self.logger.info(f'start scraping old data...')
            previous_table_list = get_old_table_list(self.old_table_database, get_table_suffix_condition())

            temp_table_name = self.prefix + table_name

            if temp_table_name in previous_table_list:

                old_df = get_old_data(self.old_table_database, temp_table_name)
                dump_df = merge_data(old_df, new_df, logger=self.logger, now=now)

                if dump_df.duplicated().any():
                    self.logger.error(dump_df[dump_df.duplicated()])
                    raise ValueError("dump dataset should not have duplicated row")

                self.logger.info(f'start creating table {temp_table_name}...')
                create_new_table(temp_table_name, self.dump_database)

                self.logger.info(f'start writing data in to {temp_table_name}...')
                write_into_table(dump_df, self.dump_database, temp_table_name)

            else:
                self.logger.info(f'there is no {temp_table_name}, directly dumping...')
                dump_df = clean_rest(new_df, now=now)

                if dump_df.duplicated().any():
                    self.logger.error(dump_df[dump_df.duplicated()])
                    raise ValueError("dump dataset should not have duplicated row")

                self.logger.info(f'start creating table {temp_table_name}...')
                create_new_table(temp_table_name, self.dump_database)

                self.logger.info(f'start writing data in to {temp_table_name}...')
                write_into_table(dump_df, self.dump_database, temp_table_name)

def state_checker(state_list: List[Dict]) -> None:
    for i in state_list:
        if i.get('prod_stat') not in ('finish', 'no_data'):
            raise TaskUnfinishedError(f"task {i.get('task_id')} is unfinished")

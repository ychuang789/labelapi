from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict

from settings import TABLE_PREFIX, CONFLICT_GROUPS
from utils.helper import get_logger


class IGroups(ABC):
    def __init__(self, task_ids: List[str], input_database: str,
                 output_database: str, generate_dict: defaultdict,
                 result_table_dict: defaultdict,
                 previous_year: int,
                 logger_name: str = "IGroups",
                 prefix: str = TABLE_PREFIX,
                 conflict_term: str = None):
        self.task_ids = task_ids
        self.generate_dict = generate_dict
        self.result_table_dict = result_table_dict
        self.input_database = input_database
        self.output_database = output_database
        self.previous_year = previous_year
        self.logger = get_logger(logger_name)
        self.prefix = prefix
        self.conflict_term = conflict_term

    @abstractmethod
    def get_generate_dict(self) -> Dict[str,List[str]]:
        """get the dict of output table with target result
        i.e. {"social":[task_id1, task_id2 ... task_idn],}"""
        pass

    @abstractmethod
    def run_merge(self) -> None:
        """run the merge function to add previous data"""
        pass

    @abstractmethod
    def dump_zip(self) -> None:
        """dump to zip"""
        pass

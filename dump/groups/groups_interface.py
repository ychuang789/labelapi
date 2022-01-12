from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict, Tuple, Union

from settings import TABLE_PREFIX
from utils.general_helper import get_logger


class IGroups(ABC):
    def __init__(self, id_list: Union[List[str],List[int]],
                 old_table_database: str,
                 new_table_database: str,
                 dump_database: str,
                 generate_dict: defaultdict,
                 result_table_dict: defaultdict,
                 logger_name: str = "IGroups",
                 verbose: bool = False,
                 prefix: str = TABLE_PREFIX
                 ):
        self.id_list = id_list
        self.generate_dict = generate_dict
        self.result_table_dict = result_table_dict
        self.old_table_database = old_table_database
        self.new_table_database = new_table_database
        self.dump_database = dump_database
        self.logger = get_logger(logger_name, verbose=verbose)
        self.prefix = prefix

    @abstractmethod
    def get_generate_dict(self) -> Dict[str,List[str]]:
        """get the dict of output table with target result
        i.e. {"social":[task_id1, task_id2 ... task_idn],}"""
        pass

    @abstractmethod
    def run_merge(self) -> None:
        """run the merge function to add previous data"""
        pass



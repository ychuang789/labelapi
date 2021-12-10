from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict

from utils.helper import get_logger


class IGroups(ABC):
    def __init__(self, task_ids: List[str], input_database: str,
                 output_database: str, generate_dict: defaultdict,
                 logger_name: str = "IGroups"):
        self.task_ids = task_ids
        self.generate_dict = generate_dict
        self.input_database = input_database
        self.output_database = output_database
        self.logger = get_logger(logger_name)

    @abstractmethod
    def get_generate_dict(self) -> Dict[str,List[str]]:
        """get the dict of output table with target result
        i.e. {"social":[task_id1, task_id2 ... task_idn],}"""
        pass

    @abstractmethod
    def run_merge(self) -> None:
        """run the merge function to add previous data"""
        pass

import os
from datetime import datetime

from definition import AUDIENCE_PRODUCTION_PATH
from settings import DatabaseConfig


class ResultMissingError(Exception):
    """result cannot be trace from TABLE_GROUPS_FOR_INDEX"""
    pass

class TaskUnfinishedError(Exception):
    """prod_stat is not `finish` in state"""
    pass

class OutputZIPNotFoundError(Exception):
    """output ZIP file not found"""
    pass


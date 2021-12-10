class ResultMissingError(Exception):
    """result cannot be trace from TABLE_GROUPS_FOR_INDEX"""
    pass

class TaskUnfinishedError(Exception):
    """prod_stat is not `finish` in state"""
    pass

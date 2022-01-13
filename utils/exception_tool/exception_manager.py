class DataNotFoundError(Exception):
    """nothing return from database"""
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(self), (self.msg)

class ResultMissingError(Exception):
    """result cannot be trace from TABLE_GROUPS_FOR_INDEX"""
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(self), (self.msg)

class TaskUnfinishedError(Exception):
    """prod_stat is not `finish` in state"""
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(self), (self.msg)

class OutputZIPNotFoundError(Exception):
    """output ZIP file not found"""
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(self), (self.msg)

class ModelTypeNotFoundError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(ModelTypeNotFoundError), (self.msg)

class ParamterMissingError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(ModelTypeNotFoundError), (self.msg)

class TWFeatureModelNotFoundError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
    def __reduce__(self):
        return type(self), (self.msg)

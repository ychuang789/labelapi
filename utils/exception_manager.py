class DataNotFoundError(Exception):
    """nothing return from database"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return DataNotFoundError, (self.msg,)

class ResultMissingError(Exception):
    """result cannot be trace from TABLE_GROUPS_FOR_INDEX"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return ResultMissingError, (self.msg,)

class TaskUnfinishedError(Exception):
    """prod_stat is not `finish` in state"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return TaskUnfinishedError, (self.msg,)

class OutputZIPNotFoundError(Exception):
    """output ZIP file not found"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return OutputZIPNotFoundError, (self.msg,)

class ModelTypeNotFoundError(Exception):
    """wrong model type input from api"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return ModelTypeNotFoundError, (self.msg,)

class ParamterMissingError(Exception):
    """missing kwargs like patterns"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return ParamterMissingError, (self.msg,)

class TWFeatureModelNotFoundError(Exception):
    """tw model is not found, plz refer to TWFeatureModel in utils.enum_config"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
    def __reduce__(self):
        return TWFeatureModelNotFoundError, (self.msg,)

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


class ModelTypeError(Exception):
    """wrong model type implement"""

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __reduce__(self):
        return ModelTypeError, (self.msg,)


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


class DataMissingError(Exception):
    """Target data is not exist"""

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __reduce__(self):
        return DataMissingError, (self.msg,)


class UploadModelError(Exception):
    """Error about uploading model"""

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __reduce__(self):
        return UploadModelError, (self.msg,)


class RequestValidationError(Exception):
    """use in verify the request body"""

    def __init__(self, msg):
        self.msg = msg

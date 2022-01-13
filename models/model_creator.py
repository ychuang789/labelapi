# import importlib
# from typing import Union
#
# from models.audience_model_interfaces import RuleBaseModel, SupervisedModel
# from settings import MODEL_INFORMATION
# from utils.enum_config import ModelType, PredictTarget
#
# class ModelTypeNotFoundError(Exception):
#     def __init__(self, msg):
#         super().__init__()
#         self.msg = msg
#     def __reduce__(self):
#         return type(ModelTypeNotFoundError), (self.msg)
#
# class ParamterMissingError(Exception):
#     def __init__(self, msg):
#         super().__init__()
#         self.msg = msg
#     def __reduce__(self):
#         return type(ModelTypeNotFoundError), (self.msg)
#
# class ModelSelector():
#     """Select a model and create it"""
#
#     def __init__(self, model_name: Union[str, ModelType], target_name: Union[str, PredictTarget],
#                  is_train = True, **kwargs):
#         self.model_name = model_name if isinstance(model_name, str) else model_name.value
#         self.target_name = target_name.lower() if isinstance(target_name, str) else target_name.value
#         self.model_path = kwargs.pop('model_path', None)
#         self.pattern = kwargs.pop('patterns', None)
#         self.is_train = is_train
#         self.model_info = kwargs
#
#     def get_model_class(self, model_name: str):
#         if model_name in MODEL_INFORMATION:
#             module_path, class_name = MODEL_INFORMATION.get(model_name).rsplit(sep='.', maxsplit=1)
#             return getattr(importlib.import_module(module_path), class_name), class_name
#         else:
#             raise ModelTypeNotFoundError(f'{model_name} is not a available model')
#
#     def create_model_obj(self):
#         try:
#             model_class, class_name = self.get_model_class(self.model_name)
#         except ModelTypeNotFoundError:
#             raise ModelTypeNotFoundError(f'{self.model_name} is not a available model')
#
#         if model_class:
#             self.model = model_class(model_dir_name=self.model_path, feature=self.target_name)
#         else:
#             raise ValueError(f'model_name {self.model_name} is unknown')
#
#         if not self.is_train:
#             if isinstance(self.model, SupervisedModel):
#                 self.model.load()
#             if isinstance(self.model, RuleBaseModel):
#                 if self.pattern:
#                     self.model.load(self.pattern)
#                 else:
#                     raise ParamterMissingError(f'patterns are missing')
#
#         return self.model
#
#
#

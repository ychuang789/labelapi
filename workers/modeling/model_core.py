import importlib
import json
from datetime import datetime
from typing import Dict

from models.audience_model_interfaces import SupervisedModel, RuleBaseModel

from models.trainable_models.tw_model import TermWeightModel
from settings import MODEL_INFORMATION

from utils.data.data_helper import get_term_weights_objects
from utils.general_helper import get_logger
from utils.enum_config import ModelTaskStatus, DatasetType
from utils.exception_tool.exception_manager import ModelTypeNotFoundError, ParamterMissingError
from workers.modeling.preprocess_core import PreprocessWorker

from workers.orm_core.model_operation import ModelingCRUD


class ModelingWorker():
    def __init__(self, model_name: str, predict_type: str,
                 dataset_number: int = None, dataset_schema: str = None,
                 orm_cls: ModelingCRUD = None, preprocess: PreprocessWorker = None, logger_name: str = 'modeling',
                 verbose: bool = False, **model_information):
        super().__init__(model_name=model_name, predict_type=predict_type,
                         dataset_number=dataset_number, dataset_schema=dataset_schema,
                         logger_name=logger_name, verbose=verbose, _preprocessor=None)
        self.model = None
        self.model_name = model_name
        self.predict_type = predict_type
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema
        self.logger = get_logger(logger_name, verbose=verbose)
        self.model_information = model_information
        self.orm_cls = orm_cls if orm_cls else ModelingCRUD(echo=verbose)
        self.preprocess = preprocess if preprocess \
            else PreprocessWorker(dataset_number=self.dataset_number,dataset_schema=self.dataset_schema)

    def run_task(self, task_id: str, job_id: int = None) -> None:

        ms = self.orm_cls.ms
        mr = self.orm_cls.mr

        try:
            if self.orm_cls.session.query(ms).filter(ms.job_id == job_id).all():
                self.orm_cls.model_delete_record(model_job_id=job_id)
            self.add_task_info(task_id=task_id, job_id=job_id, ext_test=False)

            self.logger.info(f"start modeling task: {task_id}")
            self.logger.info(f'Initializing the model {self.model_name.lower()}...')
            self.init_model()

            if not hasattr(self.model, 'fit'):
                err_msg = f'{self.model.name} is not trainable'
                self.logger.error(err_msg)
                self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update(
                    {ms.training_status: ModelTaskStatus.UNTRAINABLE.value,
                     ms.error_message: err_msg})
                self.orm_cls.session.commit()
                return

            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update(
                {ms.training_status: ModelTaskStatus.STARTED.value})
            self.orm_cls.session.commit()

            self.logger.info(f'preparing the datasets for task: {task_id}')
            self.data_preprocess()
            self.model.fit(self.training_set, self.training_y, **self.model_information)

            if isinstance(self.model, TermWeightModel):
                bulk_list = get_term_weights_objects(task_id, self.model.label_term_weights)
                self.orm_cls.session.bulk_save_objects(bulk_list)
                # self.orm_cls.session.add_all(bulk_list)
                self.orm_cls.session.commit()

            self.logger.info(f"evaluating the model ...")
            dev_report = self.model.eval(self.dev_set, self.dev_y)
            self.orm_cls.session.add(mr(task_id=task_id,
                                        dataset_type=DatasetType.DEV.value,
                                        accuracy=dev_report.get('accuracy'),
                                        report=json.dumps(dev_report, ensure_ascii=False),
                                        create_time=datetime.now()
                                        ))
            self.logger.info(f"testing the model ...")
            test_report = self.model.eval(self.testing_set, self.testing_y)
            self.orm_cls.session.add(mr(task_id=task_id,
                                        dataset_type=DatasetType.TEST.value,
                                        accuracy=test_report.get('accuracy'),
                                        report=json.dumps(test_report, ensure_ascii=False),
                                        create_time=datetime.now()
                                        ))
            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({
                ms.training_status: ModelTaskStatus.FINISHED.value
            })
            self.orm_cls.session.commit()
            self.logger.info(f"modeling task: {task_id} is finished")
        except Exception as e:
            self.orm_cls.session.rollback()
            err_msg = f"modeling task: {task_id} is failed since {e}"
            self.logger.error(err_msg)
            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({ms.training_status: ModelTaskStatus.FAILED.value,
                                                                                 ms.error_message: err_msg})
            self.orm_cls.session.commit()
            raise e
        finally:
            self.orm_cls.dispose()

    def eval_outer_test_data(self, job_id: int) -> None:

        ms = self.orm_cls.ms
        mr = self.orm_cls.mr

        if not (result := self.orm_cls.session.query(ms).filter(ms.job_id == job_id).first()):
            err_msg = f'Model is not train or prepare yet, execute training API first'
            self.orm_cls.dispose()
            raise ValueError(err_msg)
        else:
            task_id = result.task_id
            self.add_task_info(task_id=task_id, ext_test=True)

        try:
            self.logger.info(f"start eval_outer_test_data task: {task_id}")
            self.logger.info(f"load the model {self.model_information.get('model_path', None)} ...")
            if not self.model:
                self.logger.info(f'Initializing the model {self.model_name.lower()}...')
                self.init_model(is_train=False)

            if not hasattr(self.model, 'eval'):
                err_msg = f'{self.model.name} cannot be evaluated'
                self.logger.error(err_msg)
                self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update(
                    {ms.training_status: ModelTaskStatus.FAILED.value, ms.error_message: err_msg})
                self.orm_cls.session.commit()
                return

            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update(
                {ms.ext_status: ModelTaskStatus.STARTED.value})
            self.orm_cls.session.commit()

            self.logger.info(f'preparing the datasets for task: {task_id}')
            self.data_preprocess(is_train=False)

            self.logger.info(f"evaluating with ext_test data ...")
            report = self.model.eval(self.testing_set, self.testing_y)

            self.orm_cls.session.add(mr(task_id=task_id,
                                        dataset_type=DatasetType.EXT_TEST.value,
                                        accuracy=report.get('accuracy', -1),
                                        report=json.dumps(report, ensure_ascii=False),
                                        create_time=datetime.now()
                                        ))

            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({
                ms.ext_status: ModelTaskStatus.FINISHED.value
            })
            self.orm_cls.session.commit()
            self.logger.info(f"modeling task: {task_id} is finished")

        except FileNotFoundError as f:
            self.orm_cls.session.rollback()
            err_msg = f"modeling task: {task_id} is failed since {f}"
            self.logger.error(err_msg)
            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({ms.ext_status: ModelTaskStatus.FAILED.value,
                                                                                 ms.error_message: err_msg})
            self.orm_cls.session.commit()
            raise f
        except Exception as e:
            self.orm_cls.session.rollback()
            err_msg = f"modeling task: {task_id} is failed since {e}"
            self.logger.error(err_msg)
            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({ms.ext_status: ModelTaskStatus.FAILED.value,
                                                                                 ms.error_message: err_msg})
            self.orm_cls.session.commit()
            raise e
        finally:
            self.orm_cls.dispose()

    def init_model(self, is_train=True) -> None:
        try:
            self.model = self.create_model_obj(is_train=is_train)
        except ModelTypeNotFoundError:
            err_msg = f'{self.model_name} is not a available model'
            self.logger.error(err_msg)
            raise ModelTypeNotFoundError(err_msg)
        except ParamterMissingError as p:
            err_msg = f'{self.model_name} model parameter `{p}` is missing in `MODEL_INFO`'
            self.logger.error(err_msg)
            raise ParamterMissingError(err_msg)
        except Exception as e:
            self.logger.error(e)
            raise e

    def get_model_class(self, model_name: str):
        if model_name in MODEL_INFORMATION:
            module_path, class_name = MODEL_INFORMATION.get(model_name).rsplit(sep='.', maxsplit=1)
            return getattr(importlib.import_module(module_path), class_name), class_name
        else:
            raise ModelTypeNotFoundError(f'{model_name} is not a available model')

    def create_model_obj(self, is_train: bool):
        self.model_path = self.model_information.get('model_path', None)
        self.pattern = self.model_information.get('patterns', None)
        self.target_name = self.predict_type.lower()
        try:
            model_class, class_name = self.get_model_class(self.model_name)
        except ModelTypeNotFoundError:
            raise ModelTypeNotFoundError(f'{self.model_name} is not a available model')

        if model_class:
            self.model = model_class(model_dir_name=self.model_path, feature=self.target_name)
        else:
            raise ValueError(f'model_name {self.model_name} is unknown')

        if not is_train:
            if isinstance(self.model, SupervisedModel):
                self.model.load()
            if isinstance(self.model, RuleBaseModel):
                if self.pattern:
                    self.model.load(self.pattern)
                else:
                    raise ParamterMissingError(f'patterns are missing')

        return self.model


    def add_task_info(self, task_id, job_id=None, ext_test=False):

        ms = self.orm_cls.mr

        try:
            if not ext_test:
                self.orm_cls.session.add(ms(task_id=task_id,
                                            model_name=self.model_name,
                                            training_status=ModelTaskStatus.PENDING.value,
                                            feature=self.predict_type,
                                            model_path=self.model_information.get('model_path'),
                                            create_time=datetime.now(),
                                            job_id=job_id
                                            ))
                self.orm_cls.session.commit()
            else:
                self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({ms.ext_status: ModelTaskStatus.PENDING.value})
                self.orm_cls.session.commit()
        except Exception as e:
            self.orm_cls.session.rollback()
            self.orm_cls.dispose()
            raise e

    def data_preprocess(self, is_train: bool = True):
        if is_train:
            dataset: Dict = self.preprocess.run_processing()

            self.training_set = dataset.get(DatasetType.TRAIN.value)
            self.training_y = [[d.label] for d in self.training_set]
            self.dev_set = dataset.get(DatasetType.DEV.value)
            self.dev_y = [[d.label] for d in self.dev_set]
            self.testing_set = dataset.get(DatasetType.TEST.value)
            self.testing_y = [[d.label] for d in self.testing_set]

            self.logger.info(f'training_set: {len(self.training_set)}')
            self.logger.info(f'dev_set: {len(self.dev_set)}')
            self.logger.info(f'testing_set: {len(self.testing_set)}')
        else:
            dataset = self.preprocess.run_processing(is_train=False)
            self.testing_set = dataset
            self.testing_y = [[d.label] for d in self.testing_set]




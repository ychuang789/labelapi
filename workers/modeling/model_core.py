import csv
import importlib
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict

from models.audience_model_interfaces import SupervisedModel, RuleBaseModel

from models.trainable_models.tw_model import TermWeightModel
from settings import MODEL_INFORMATION
from utils.data.data_download import pre_check

from utils.data.data_helper import get_term_weights_objects, get_term_weights_from_file
from utils.general_helper import get_logger
from utils.enum_config import ModelTaskStatus, DatasetType, ModelType
from utils.exception_manager import ModelTypeNotFoundError, ParamterMissingError, UploadModelError
from workers.preprocessing.preprocess_core import PreprocessWorker

from workers.orm_core.model_operation import ModelingCRUD
from workers.orm_core.table_creator import EvalDetails


class ModelingWorker:
    def __init__(self, task_id: str, model_name: str, predict_type: str, dataset_number: int = None,
                 dataset_schema: str = None, orm_cls: ModelingCRUD = None, preprocess: PreprocessWorker = None,
                 logger_name: str = 'modeling', verbose: bool = False, **model_information):
        self.model = None
        self.task_id = task_id
        self.model_name = model_name
        self.predict_type = predict_type
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema
        self.logger = get_logger(logger_name, verbose=verbose)
        self.model_information = model_information
        self.orm_cls = orm_cls if orm_cls else ModelingCRUD(echo=verbose)
        self.preprocess = preprocess if preprocess \
            else PreprocessWorker(dataset_number=self.dataset_number, dataset_schema=self.dataset_schema)
        self.target_name = self.predict_type.lower()
        self.model_path = self.model_information.get('model_path', None)

    def run_task(self) -> None:

        ms = self.orm_cls.ms
        mr = self.orm_cls.mr

        try:
            if self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).all():
                self.orm_cls.delete_record(task_id=self.task_id)
            self.add_task_info(ext_test=False)

            self.logger.info(f"start modeling task: {self.task_id}")
            self.logger.info(f'Initializing the model {self.model_name.lower()}...')
            self.init_model()

            if not hasattr(self.model, 'fit'):
                err_msg = f'{self.model.name} is not trainable'
                self.logger.error(err_msg)
                self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).update(
                    {ms.training_status: ModelTaskStatus.UNTRAINABLE.value,
                     ms.error_message: err_msg})
                self.orm_cls.session.commit()
                return

            self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).update(
                {ms.training_status: ModelTaskStatus.STARTED.value})
            self.orm_cls.session.commit()

            self.logger.info(f'preparing the datasets for task: {self.task_id}')
            self.data_preprocess()
            self.model.fit(self.training_set, self.training_y, **self.model_information)

            if isinstance(self.model, TermWeightModel):
                bulk_list = get_term_weights_objects(self.task_id, self.model.label_term_weights)
                self.orm_cls.session.bulk_save_objects(bulk_list)
                self.orm_cls.session.commit()

            self.logger.info(f"evaluating the model ...")
            dev_report, dev_predict_labels = self.model.eval(self.dev_set, self.dev_y)
            dev_report_cls = mr(task_id=self.task_id,
                                dataset_type=DatasetType.DEV.value,
                                accuracy=dev_report.get('accuracy'),
                                report=json.dumps(dev_report, ensure_ascii=False),
                                create_time=datetime.now()
                                )
            self.orm_cls.session.add(dev_report_cls)

            self.logger.info(f"testing the model ...")
            test_report, test_predict_labels = self.model.eval(self.testing_set, self.testing_y)
            test_report_cls = mr(task_id=self.task_id,
                                 dataset_type=DatasetType.TEST.value,
                                 accuracy=test_report.get('accuracy'),
                                 report=json.dumps(test_report, ensure_ascii=False),
                                 create_time=datetime.now()
                                 )
            self.orm_cls.session.add(test_report_cls)

            self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).update({
                ms.training_status: ModelTaskStatus.FINISHED.value
            })
            self.orm_cls.session.commit()

            # bulk save eval_details
            self.logger.info(f"saving eval_details ...")
            dev_eval_details_bulk_list = self.bulk_insert_eval_details(dataset=self.dev_set,
                                                                       y_pred=dev_predict_labels,
                                                                       report_id=dev_report_cls.id)
            self.orm_cls.session.bulk_save_objects(dev_eval_details_bulk_list)

            test_eval_details_bulk_list = self.bulk_insert_eval_details(dataset=self.testing_set,
                                                                        y_pred=test_predict_labels,
                                                                        report_id=test_report_cls.id)
            self.orm_cls.session.bulk_save_objects(test_eval_details_bulk_list)

            self.orm_cls.session.commit()

            self.write_csv(dataset=self.dev_set, y_pred=dev_predict_labels, setname='dev')
            self.write_csv(dataset=self.testing_set, y_pred=test_predict_labels, setname='test')

            self.logger.info(f"modeling task: {self.task_id} is finished")
        except Exception as e:
            self.orm_cls.session.rollback()
            err_msg = f"modeling task: {self.task_id} is failed since {e}"
            self.logger.error(err_msg)
            self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).update(
                {ms.training_status: ModelTaskStatus.FAILED.value,
                 ms.error_message: err_msg})
            self.orm_cls.session.commit()
            raise e
        finally:
            self.orm_cls.dispose()

    def eval_outer_test_data(self) -> None:

        ms = self.orm_cls.ms
        mr = self.orm_cls.mr

        if not (result := self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).first()):
            err_msg = f'Model is not train or prepare yet, execute training API first'
            self.orm_cls.dispose()
            raise ValueError(err_msg)
        else:
            task_id = result.task_id
            self.add_task_info(ext_test=True)

        try:
            self.logger.info(f"start eval_outer_test_data task: {task_id}")
            self.logger.info(f"load the model {self.model_path} ...")
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
            report, predict_labels = self.model.eval(self.testing_set, self.testing_y)

            test_report_cls = mr(task_id=task_id,
                                 dataset_type=DatasetType.EXT_TEST.value,
                                 accuracy=report.get('accuracy', -1),
                                 report=json.dumps(report, ensure_ascii=False),
                                 create_time=datetime.now()
                                 )

            self.orm_cls.session.add(test_report_cls)

            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update({
                ms.ext_status: ModelTaskStatus.FINISHED.value
            })
            self.orm_cls.session.commit()

            self.logger.info(f"saving eval_details ...")
            test_eval_details_bulk_list = self.bulk_insert_eval_details(dataset=self.testing_set,
                                                                        y_pred=predict_labels,
                                                                        report_id=test_report_cls.id)
            self.orm_cls.session.bulk_save_objects(test_eval_details_bulk_list)

            self.orm_cls.session.commit()

            self.write_csv(dataset=self.testing_set, y_pred=predict_labels, setname='ext_test')

            self.logger.info(f"modeling task: {task_id} is finished")

        except FileNotFoundError as f:
            self.orm_cls.session.rollback()
            err_msg = f"modeling task: {task_id} is failed since {f}"
            self.logger.error(err_msg)
            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update(
                {ms.ext_status: ModelTaskStatus.FAILED.value,
                 ms.error_message: err_msg})
            self.orm_cls.session.commit()
            raise f
        except Exception as e:
            self.orm_cls.session.rollback()
            err_msg = f"modeling task: {task_id} is failed since {e}"
            self.logger.error(err_msg)
            self.orm_cls.session.query(ms).filter(ms.task_id == task_id).update(
                {ms.ext_status: ModelTaskStatus.FAILED.value,
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

    def get_model_class(self):
        if self.model_name in MODEL_INFORMATION:
            module_path, class_name = MODEL_INFORMATION.get(self.model_name).rsplit(sep='.', maxsplit=1)
            return getattr(importlib.import_module(module_path), class_name), class_name
        else:
            raise ModelTypeNotFoundError(f'{self.model_name} is not a available model')

    def create_model_obj(self, is_train: bool):
        try:
            model_class, class_name = self.get_model_class()
        except ModelTypeNotFoundError:
            raise ModelTypeNotFoundError(f'{self.model_name} is not a available model')

        if model_class:
            self.model = model_class(model_dir_name=self.model_path, feature=self.target_name)
        else:
            raise ValueError(f'model_name {self.model_name} is unknown')

        if not is_train:
            if isinstance(self.model, SupervisedModel):
                if self.model_name == ModelType.TERM_WEIGHT_MODEL.name:
                    term_weight_set = self.orm_cls.get_term_weight_set(task_id=self.task_id)['data']
                    label_term_weights = self.preprocess.load_term_weight_from_db(term_weight_set)
                    self.model.load(label_term_weights=label_term_weights)
                else:
                    self.model.load()
            if isinstance(self.model, RuleBaseModel):
                rules = self.orm_cls.get_rules(task_id=self.task_id)
                if not rules or len(rules) == 0:
                    raise ParamterMissingError(f'patterns are missing')
                rules_dict = defaultdict(list)
                for rule in rules:
                    if self.model_name == ModelType.REGEX_MODEL.name:
                        rules_dict[rule.label].append(str(rule.content))
                    elif self.model_name == ModelType.KEYWORD_MODEL.name:
                        rules_dict[rule.label].append((rule.content, rule.match_type))
                    else:
                        raise ValueError(f"{rule.rule_type} is not a proper rule type for the task")
                self.model.load(rules_dict)
        else:
            if isinstance(self.model, RuleBaseModel):
                self.logger.info("Write the rules into backend database")
                bulk_rules = self.preprocess.get_rules(self.task_id)
                if not bulk_rules:
                    raise ValueError("Rules are not found")
                try:
                    self.orm_cls.session.bulk_save_objects(bulk_rules)
                    self.orm_cls.session.commit()
                except Exception as e:
                    self.orm_cls.session.rollback()
                    raise e

        return self.model

    def add_task_info(self, ext_test=False):
        ms = self.orm_cls.ms
        try:
            if not ext_test:
                self.orm_cls.session.add(ms(task_id=self.task_id,
                                            model_name=self.model_name,
                                            training_status=ModelTaskStatus.PENDING.value,
                                            feature=self.predict_type,
                                            model_path=self.model_path,
                                            create_time=datetime.now()
                                            ))
                self.orm_cls.session.commit()
            else:
                self.orm_cls.session.query(ms).filter(ms.task_id == self.task_id).update(
                    {ms.ext_status: ModelTaskStatus.PENDING.value})
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

    def bulk_insert_eval_details(self, dataset, y_pred, report_id):
        bulk_list = []
        for data, y in zip(dataset, y_pred):
            bulk_list.append(
                EvalDetails(
                    doc_id=data.id_,
                    content=getattr(data, self.target_name),
                    ground_truth=data.label,
                    predict_label=y if not isinstance(y, list) else ','.join(y),
                    task_id=self.task_id,
                    report_id=report_id
                )
            )
        return bulk_list

    def write_csv(self, dataset, y_pred, setname):
        filename = f'{self.model_name.lower()}_{self.task_id}_{setname}.csv'
        filepath = pre_check(filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            fieldnames = ['doc_id', 'content', 'ground_truth', 'predict_label']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for data, y in zip(dataset, y_pred):
                writer.writerow({
                    'doc_id': data.id_,
                    'content': getattr(data, self.target_name),
                    'ground_truth': data.label,
                    'predict_label': y
                })

    @staticmethod
    def import_term_weights(filepath: str, filename:str, task_id: str):
        orm_worker = ModelingCRUD()

        upload_model = orm_worker.upload_model
        id_ = orm_worker.start_upload_model_to_table(task_id=task_id,
                                                     filename=filename)

        try:
            if not orm_worker.session.query(orm_worker.ms).get(task_id):
                raise ValueError(f"Model {task_id} is not trained yet.")
            else:
                previous_term_weight_set = orm_worker.session.query(orm_worker.tw).filter(
                    orm_worker.tw.task_id == task_id)
                previous_term_weight_set.delete()
                orm_worker.session.commit()
            csv_rows = PreprocessWorker.read_csv_file(filepath)
            term_weight_bulk_list = get_term_weights_from_file(task_id=task_id, term_weight_list=csv_rows)
            orm_worker.session.bulk_save_objects(term_weight_bulk_list)
            orm_worker.session.query(upload_model).filter(upload_model.id == id_).update(
                {upload_model.status: ModelTaskStatus.FINISHED.value}
            )

            orm_worker.session.query(orm_worker.ms).filter(
                orm_worker.ms.task_id == task_id).update(
                {orm_worker.ms.training_status: ModelTaskStatus.FINISHED.value}
            )

            orm_worker.session.commit()
        except Exception as e:
            orm_worker.session.rollback()
            err_msg = f"{task_id} failed to upload term weight since {e}"
            orm_worker.session.query(upload_model).filter(upload_model.id == id_).update(
                {upload_model.status: ModelTaskStatus.FAILED.value,
                 upload_model.error_message: err_msg}
            )
            orm_worker.session.query(orm_worker.ms).filter(
                orm_worker.ms.task_id == task_id).update(
                {orm_worker.ms.training_status: ModelTaskStatus.FAILED.value}
            )
            orm_worker.session.commit()
            raise UploadModelError(err_msg)
        finally:
            orm_worker.dispose()

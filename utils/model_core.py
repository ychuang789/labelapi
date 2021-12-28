import json
from datetime import datetime
from typing import Dict

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from models.audience_data_interfaces import PreprocessInterface
from models.model_creator import ModelCreator, ModelTypeNotFoundError, ParamterMissingError
from models.tw_model import TermWeightModel
from settings import DatabaseConfig
from utils.data_helper import get_term_weights_objects
from utils.helper import get_logger
from utils.selections import ModelType

class ModelingWorker(PreprocessInterface):
    """
    Training, validation and testing the model, auto-load the model while initializing.
    Using data preprocessing adaptor to scrape, transform, preprocess the dataset before modeling.
    Saving the modeling status and report to `audience_result`.modeling_status and `audience_result`.modeling_report
    """
    def __init__(self, model_name: str, predict_type: str,
                 dataset_number: int, dataset_schema: str, logger_name: str = 'modeling',
                 verbose = False, **model_information):
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
        if not self.model:
            self.logger.info(f'Initializing the model {model_name.lower()}...')
            self.init_model(self.model_name, self.predict_type, **self.model_information)

    def run_task(self, task_id: str, sql_debug=False) -> None:

        if not hasattr(self.model, 'fit'):
            err_msg = f'{self.model.name} is not trainable'
            self.logger.error(err_msg)
            raise AttributeError(err_msg)

        try:
            engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=sql_debug)
        except Exception as e:
            err_msg = f'connection failed, additional error message {e}'
            self.logger.error(err_msg)
            raise e

        session = Session(engine, autoflush=False)
        meta = MetaData()
        meta.reflect(engine, only=['model_status', 'model_report', 'term_weights'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        # build table cls
        ms = Base.classes.model_status
        mr = Base.classes.model_report
        # tw = Base.classes.term_weights

        self.logger.info(f"start modeling task: {task_id}")

        session.query(ms).filter(ms.task_id == task_id).update({ms.training_status: 'started'})


        try:
            self.logger.info(f'preparing the datasets for task: {task_id}')
            self.data_preprocess()
        except Exception as e:
            err_msg = f'failed to prepare the dataset for the model since {e}'
            self.logger.error(err_msg)
            raise e

        try:
            self.model.fit(self.training_set, self.training_y)

            if isinstance(self.model, TermWeightModel):
                bulk_list = get_term_weights_objects(task_id, self.model.label_term_weights)
                session.add_all(bulk_list)

                # session.bulk_save_objects(bulk_list)

            self.logger.info(f"evaluating the model ...")
            dev_report = self.model.eval(self.dev_set, self.dev_y)
            session.add(mr(task_id=task_id,
                           dataset_type='dev',
                           accuracy=dev_report.get('accuracy', -1),
                           report=json.dumps(dev_report, ensure_ascii=False),
                           create_time=datetime.now()
                           ))
            self.logger.info(f"testing the model ...")
            test_report = self.model.eval(self.testing_set, self.testing_y)
            session.add(mr(task_id=task_id,
                           dataset_type='test',
                           accuracy=test_report.get('accuracy', -1),
                           report=json.dumps(test_report, ensure_ascii=False),
                           create_time=datetime.now()
                           ))
            session.query(ms).filter(ms.task_id == task_id).update({
                ms.training_status: "finished"
            })
            session.commit()
            self.logger.info(f"modeling task: {task_id} is finished")
        except Exception as e:
            session.rollback()
            session.query(ms).filter(ms.task_id==task_id).update({ms.training_status:'failed'})
            session.commit()
            err_msg = f"modeling task: {task_id} is failed since {e}"
            self.logger.error(err_msg)
            raise e
        finally:
            session.close()
            engine.dispose()

    def eval_outer_test_data(self, task_id: str, sql_debug=False) -> None:

        if not hasattr(self.model, 'eval'):
            err_msg = f'{self.model.name} cannot be evaluated'
            self.logger.error(err_msg)
            raise AttributeError(err_msg)

        try:
            engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=sql_debug)
        except Exception as e:
            err_msg = f'connection failed, additional error message {e}'
            self.logger.error(err_msg)
            raise e

        session = Session(engine, autoflush=False)
        meta = MetaData()
        meta.reflect(engine, only=['model_status', 'model_report', 'term_weights'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        # build table cls
        ms = Base.classes.model_status
        mr = Base.classes.model_report


        self.logger.info(f"start eval_outer_test_data task: {task_id}")

        session.query(ms).filter(ms.task_id == task_id).update({ms.ext_status: 'started'})

        try:
            self.logger.info(f'preparing the datasets for task: {task_id}')
            self.data_preprocess(is_train=False)
        except Exception as e:
            err_msg = f'failed to prepare the dataset for the model since {e}'
            self.logger.error(err_msg)
            raise e

        try:
            self.logger.info(f"load the model {self.model_information.get('model_path', None)} ...")
            self.model.load()

            self.logger.info(f"evaluating with ext_test data ...")
            report = self.model.eval(self.testing_set, self.testing_y)

            session.add(mr(task_id=task_id,
                           dataset_type='ext_test',
                           accuracy=report.get('accuracy', -1),
                           report=json.dumps(report, ensure_ascii=False),
                           create_time=datetime.now()
                           ))

            session.query(ms).filter(ms.task_id == task_id).update({
                ms.ext_status: "finished"
            })
            session.commit()
            self.logger.info(f"modeling task: {task_id} is finished")

        except FileNotFoundError as f:
            session.rollback()
            session.query(ms).filter(ms.task_id == task_id).update({ms.ext_status: 'failed'})
            session.commit()
            err_msg = f"modeling task: {task_id} is failed since {f}"
            self.logger.error(err_msg)
            raise f
        except Exception as e:
            session.rollback()
            session.query(ms).filter(ms.task_id == task_id).update({ms.ext_status: 'failed'})
            session.commit()
            err_msg = f"modeling task: {task_id} is failed since {e}"
            self.logger.error(err_msg)
            raise e
        finally:
            session.close()
            engine.dispose()

    def init_model(self, model_name, predict_type, **model_information) -> None:
        try:
            self.model = ModelCreator.create_model(model_name, predict_type, **model_information)
        except ModelTypeNotFoundError:
            err_msg = f'{model_name} is not found. ' \
                      f'Model_type should be in {",".join([i.name for i in ModelType])}'
            self.logger.error(err_msg)
            raise ModelTypeNotFoundError(err_msg)
        except ParamterMissingError as p:
            err_msg = f'{model_name} model parameter `{p}` is missing in `MODEL_INFO`'
            self.logger.error(err_msg)
            raise ParamterMissingError(err_msg)
        except Exception as e:
            self.logger.error(e)
            raise e

    @staticmethod
    def add_task_info(task_id, model_name, predict_type, model_path, sql_debug=False):
        try:
            engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=sql_debug)
        except Exception as e:
            err_msg = f'connection failed, additional error message {e}'
            raise e

        session = Session(engine)
        meta = MetaData()
        meta.reflect(engine, only=['model_status'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        # build table cls
        ms = Base.classes.model_status

        try:
            session.add(ms(task_id=task_id,
                           model_name=model_name,
                           training_status='pending',
                           feature=predict_type,
                           model_path=model_path,
                           create_time=datetime.now()))
            session.commit()
        except Exception as e:
            err_msg = f'failed to add a new record in model_status since {e}'
            raise e
        finally:
            session.close()
            engine.dispose()

    def data_preprocess(self, is_train: bool = True):
        if is_train:
            dataset: Dict = self._preprocessor.run_processing(self.dataset_number, self.dataset_schema)

            self.training_set = dataset.get('train')
            self.training_y = [[d.label] for d in self.training_set]
            self.dev_set = dataset.get('dev')
            self.dev_y = [[d.label] for d in self.dev_set]
            self.testing_set = dataset.get('test')
            self.testing_y = [[d.label] for d in self.testing_set]

            self.logger.info(f'training_set: {len(self.training_set)}')
            self.logger.info(f'dev_set: {len(self.dev_set)}')
            self.logger.info(f'testing_set: {len(self.testing_set)}')
        else:
            dataset = self._preprocessor.run_processing(self.dataset_number, self.dataset_schema,
                                                        is_train=False, document_type='test')
            self.testing_set = dataset
            self.testing_y = [[d.label] for d in self.testing_set]




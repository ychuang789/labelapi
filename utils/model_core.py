from datetime import datetime
from typing import Dict

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from models.audience_data_interfaces import PreprocessInterface
from models.model_creator import ModelCreator, ModelTypeNotFound, ParamterMissingError
from settings import DatabaseConfig
from utils.connection_helper import create_modeling_status_table, create_modeling_report_table
from utils.helper import get_logger
from utils.selections import ModelType

class ModelingWorker(PreprocessInterface):
    """Training, validation and testing the model"""
    def __init__(self, model_name: str, predict_type: str, model_path: str,
                 dataset_number: int, dataset_schema: str, logger_name: str = 'modeling',
                 verbose = False, **model_information):
        super().__init__(_preprocessor=None)
        self.model = None
        self.model_name = model_name
        self.predict_type = predict_type
        self.model_path = model_path
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema
        self.logger = get_logger(logger_name, verbose=verbose)
        self.model_information = model_information
        if not self.model:
            self.logger.info(f'Initializing the model {model_name.lower()}...')
            self.init_model(self.model_name, self.predict_type,**self.model_information)

    def training_model(self, task_id):
        try:
            self.logger.info(f'preparing the datasets for task: {task_id}')
            self.data_preprocess()
        except Exception as e:
            err_msg = f'failed to prepare the dataset for the model since {e}'
            self.logger.error(err_msg)
            raise err_msg

        if not hasattr(self.model, 'fit'):
            err_msg = f'{self.model.name} is not trainable due to lack of attribute "fit"'
            self.logger.error(err_msg)
            raise AttributeError(err_msg)

        create_modeling_status_table()
        create_modeling_report_table()

        try:
            engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=True)
        except Exception as e:
            err_msg = f'connection failed, additional error message {e}'
            self.logger.error(err_msg)
            raise err_msg

        session = Session(engine)
        meta = MetaData()
        meta.reflect(engine, only=['modeling_status', 'modeling_report'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        # build table cls
        ms = Base.classes.modeling_status
        mr = Base.classes.modeling_report

        self.logger.info(f"start modeling task: {task_id}")

        session.add(ms(task_id=task_id,
                       model_name=self.model_name,
                       training_status='pending',
                       feature=self.predict_type,
                       model_path=self.model_path,
                       create_time=datetime.now()))
        session.commit()

        try:
            self.logger.info(f"training the model ...")
            self.model.fit(self.training_set, self.training_y)

            self.logger.info(f"evaluating the model ...")
            dev_report = self.model.eval(self.dev_set, self.dev_y)
            session.add(mr(task_id=task_id,
                           dataset_type='dev',
                           accuracy=dev_report.get('accuracy', -1),
                           report=dev_report,
                           create_time=datetime.now()
                           ))
            self.logger.info(f"testing the model ...")
            test_report = self.model.eval(self.testing_set, self.testing_y)
            session.add(mr(task_id=task_id,
                           dataset_type='test',
                           accuracy=test_report.get('accuracy', -1),
                           report=test_report,
                           create_time=datetime.now()
                           ))
            session.query(ms).filter(ms.task_id == task_id).update({
                ms.training_status: "finished"
            })
            session.commit()
            self.logger.info(f"modeling task: {task_id} is finished")
        except Exception as e:
            session.query(ms).filter(ms.task_id==task_id).update({ms.training_status:'failed'})
            session.commit()
            err_msg = f"modeling task: {task_id} is failed since {e}"
            self.logger.error(err_msg)
            raise err_msg
        finally:
            session.close()
            engine.dispose()

    def init_model(self, model_name, predict_type, **model_information):
        try:
            self.model = ModelCreator.create_model(model_name, predict_type, **model_information)
        except ModelTypeNotFound:
            err_msg = f'{model_name} is not found. ' \
                      f'Model_type should be in {",".join([i.name for i in ModelType])}'
            self.logger.error(err_msg)
            raise ModelTypeNotFound(err_msg)
        except ParamterMissingError as p:
            err_msg = f'{model_name} model parameter `{p}` is missing in `MODEL_INFO`'
            self.logger.error(err_msg)
            raise ParamterMissingError(err_msg)
        except Exception as e:
            self.logger.error(e)
            raise e

    def data_preprocess(self):
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


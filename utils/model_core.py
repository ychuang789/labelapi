import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from models.audience_models import PreprocessInterface
from models.model_creator import ModelCreator, ModelTypeNotFound, ParamterMissingError
from settings import DatabaseConfig
from utils.connection_helper import create_modeling_status_table, create_modeling_report_table, DBConnection, \
    QueryManager, ConnectionConfigGenerator
from utils.data_helper import load_examples
from utils.selections import ModelType


class PreprocessWorker:
    def run_processing(self, dataset_number, dataset_schema, sample_count=1000):
        data_dict = {}
        for i in ['train', 'dev', 'test']:
            condition = {'labeling_job_id': dataset_number, 'document_type': i}
            data = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                              **ConnectionConfigGenerator.rd2_database(
                                                  schema=dataset_schema))
            data = load_examples(data=data, sample_count=sample_count)
            data_dict.update({i: data})
        return data_dict

class ModelWorker(PreprocessInterface):
    """Training, validation and testing the model"""
    def __init__(self, model_name: str, predict_type: str, model_path: str,
                 dataset_number: int, dataset_schema: str, **model_information):
        super().__init__(_preprocessor=None)
        self.model = None
        self.model_name = model_name
        self.predict_type = predict_type
        self.model_path = model_path
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema
        self.model_information = model_information
        if not self.model:
            self.init_model(self.model_name, self.predict_type,**self.model_information)

    def training_model(self):
        if not hasattr(self.model, 'fit'):
            raise AttributeError(f'{self.model.name} is not trainable due to lack of attribute "fit"')

        create_modeling_status_table()
        create_modeling_report_table()

        try:
            engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=True)
        except Exception as e:
            raise f'connection failed, additional error message {e}'

        meta = MetaData()
        meta.reflect(engine, only=['modeling_status', 'modeling_report'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        ms = Base.classes.modeling_status
        mr = Base.classes.modeling_report
        session = Session(engine)
        task_id = uuid.uuid1().hex

        session.add(ms(task_id=task_id,
                       model_name=self.model_name,
                       training_status='pending',
                       feature=self.predict_type,
                       model_path=self.model_path,
                       create_time=datetime.now()))
        session.commit()

        try:
            self.model.fit(self.training_set, self.training_y)
            dev_report = self.model.eval(self.dev_set, self.dev_y)

            session.add(mr(task_id=task_id,
                           dataset_type='dev',
                           accuracy=dev_report.get('accuracy', -1),
                           report=dev_report,
                           create_time=datetime.now()
                           ))

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

        except Exception as e:
            session.query(ms).filter(ms.task_id==task_id).update({ms.training_status:'failed'})
            session.commit()
            raise e

        finally:
            session.close()
            engine.dispose()

    def init_model(self, model_name, predict_type, **model_information):
        try:
            self.model = ModelCreator.create_model(model_name, predict_type, **model_information)
        except ModelTypeNotFound:
            err_msg = f'{model_name} is not found. ' \
                      f'Model_type should be in {",".join([i.name for i in ModelType])}'
            raise ModelTypeNotFound(err_msg)
        except ParamterMissingError as p:
            err_msg = f'{model_name} model parameter `{p}` is missing in `MODEL_INFO`'
            raise ParamterMissingError(err_msg)
        except Exception as e:
            raise e

    def data_preprocess(self):
        dataset: Dict = self._preprocessor.run_processing(self.dataset_number, self.dataset_schema)

        self.training_set = dataset.get('train')
        self.training_y = [[d.label] for d in self.training_set]
        self.dev_set = dataset.get('dev')
        self.dev_y = [[d.label] for d in self.dev_set]
        self.testing_set = dataset.get('test')
        self.testing_y = [[d.label] for d in self.testing_set]


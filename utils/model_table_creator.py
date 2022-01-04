from sqlalchemy import create_engine, DateTime, Column, String, Integer, ForeignKey, inspect, MetaData
from sqlalchemy.dialects.mysql import LONGTEXT, DOUBLE
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import declarative_base, relationship, Session

from settings import DatabaseConfig
from utils.selections import ModelTaskStatus, ModelRecordTable

Base = declarative_base()

class ModelStatus(Base):
    __tablename__ = ModelRecordTable.model_status.value
    task_id = Column(String(32), primary_key=True)
    model_name = Column(String(100))
    training_status = Column(String(32))
    ext_status = Column(String(32))
    feature = Column(String(32), nullable=False)
    model_path = Column(String(100))
    error_message = Column(LONGTEXT)
    create_time = Column(DateTime, nullable=False)
    # one-to-many collection
    report = relationship(
        "ModelReport",
        back_populates='model_status',
        cascade="all, delete",
        passive_deletes=True)
    term_weight = relationship(
        "TermWeights",
        back_populates='model_status',
        cascade="all, delete",
        passive_deletes=True)

    def __init__(self, task_id, model_name, training_status,
                 ext_status, feature, model_path,
                 error_message, create_time):
        self.task_id = task_id
        self.model_name = model_name
        self.training_status = training_status
        self.ext_status = ext_status
        self.feature = feature
        self.model_path = model_path
        self.error_message = error_message
        self.create_time = create_time

    def __repr__(self):
        return f"<ModelStatus({self.task_id}, {self.model_name}, {self.training_status}, " \
               f"{self.ext_status}, {self.feature}, {self.model_path}, {self.error_message}, " \
               f"{self.create_time})>"

class ModelReport(Base):
    __tablename__ = ModelRecordTable.model_report.value
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_type = Column(String(10))
    accuracy = Column(DOUBLE, nullable=False)
    report = Column(String(1000), nullable=False)
    create_time = Column(DateTime, nullable=False)
    task_id = Column(String(32), ForeignKey('model_status.task_id', ondelete="CASCADE"))

    def __init__(self, dataset_type, accuracy, report, create_time, task_id):
        self.dataset_type = dataset_type
        self.accuracy = accuracy
        self.report = report
        self.create_time = create_time
        self.task_id = task_id

    def __repr__(self):
        return f"ModelReport({self.dataset_type}, {self.accuracy}, {self.report}, " \
               f"{self.create_time}, {self.task_id})"

class TermWeights(Base):
    __tablename__ = ModelRecordTable.term_weights.value
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(100), nullable=False)
    term = Column(String(20), nullable=False)
    weight = Column(DOUBLE, nullable=False)
    task_id = Column('task_id', String(32), ForeignKey('model_status.task_id', ondelete="CASCADE"))

    def __init__(self, label, term, weight, task_id):
        self.label = label
        self.term = term
        self.weight = weight
        self.task_id = task_id

    def __repr__(self):
        return f"TermWeights({self.label}, {self.term}, {self.weight}, " \
               f"{self.task_id})"


def create_model_table() -> None:
    try:
        engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=True)
    except Exception as e:
        raise f'connection failed, additional error message {e}'

    inspector = inspect(engine)
    tables = ['model_status', 'model_report', 'term_weights']
    show_table = inspector.get_table_names()
    if set(tables).issubset(show_table):
        return
    else:
        Base.metadata.create_all(engine, checkfirst=True)
        engine.dispose()



def table_cls_maker(engine: create_engine, add_new=False):

    meta = MetaData()
    if add_new:
        meta.reflect(engine, only=['model_status'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        # build table cls
        ms = Base.classes.model_status
        return ms
    else:
        meta.reflect(engine, only=['model_status', 'model_report', 'term_weights'])
        Base = automap_base(metadata=meta)
        Base.prepare()

        # build table cls
        ms = Base.classes.model_status
        mr = Base.classes.model_report

        return ms, mr


def status_changer(model_job_id: int, status: ModelTaskStatus.BREAK = ModelTaskStatus.BREAK):
    engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO)
    session = Session(engine, autoflush=False)
    ms = table_cls_maker(engine, add_new=True)
    err_msg = f'{model_job_id} {status.value} by the external user'

    try:
        session.query(ms).filter(ms.task_id == model_job_id).update({ms.training_status: status.value,
                                                                ms.error_message: err_msg})
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        engine.dispose()


def delete_record(model_job_id: int):
    engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO)
    session = Session(engine, autoflush=False)
    ms = table_cls_maker(engine, add_new=True)
    err_msg = f'{model_job_id} delete by the external user'

    try:
        record = session.query(ms).filter(ms.job_id == model_job_id).first()
        session.delete(record)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        engine.dispose()







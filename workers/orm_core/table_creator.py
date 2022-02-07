from datetime import datetime

from sqlalchemy import create_engine, DateTime, Column, String, Integer, ForeignKey, inspect, MetaData, Float, TEXT
from sqlalchemy.dialects.mysql import LONGTEXT, DOUBLE
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import declarative_base, relationship, Session, backref

from settings import DatabaseConfig, TableName
from utils.enum_config import ModelTaskStatus

Base: declarative_base = declarative_base()


class State(Base):
    __tablename__ = TableName.state
    task_id = Column(String(32), primary_key=True)
    stat = Column(String(32), nullable=False)
    prod_stat = Column(String(10))
    model_type = Column(String(32), nullable=False)
    predict_type = Column(String(32), nullable=False)
    date_range = Column(LONGTEXT, nullable=False)
    target_schema = Column(String(32), nullable=False)
    create_time = Column(DateTime, nullable=False)
    peak_memory = Column(Float)
    length_receive_table = Column(Integer)
    length_output_table = Column(Integer)
    length_prod_table = Column(String(100))
    result = Column(TEXT)
    uniq_source_author = Column(String(100))
    rate_of_label = Column(String(100))
    run_time = Column(Float)
    check_point = Column(DateTime)
    error_message = Column(LONGTEXT)

    def __init__(self, task_id, stat, prod_stat, model_type, predict_type, date_range,
                 target_table, create_time, peak_memory, length_receive_table,
                 length_output_table, length_prod_table, result, uniq_source_author,
                 rate_of_label, run_time, check_point, error_message):
        self.task_id = task_id
        self.stat = stat
        self.prod_stat = prod_stat
        self.model_type = model_type
        self.predict_type = predict_type
        self.date_range = date_range
        self.target_schema = target_table
        self.create_time = create_time
        self.peak_memory = peak_memory
        self.length_receive_table = length_receive_table
        self.length_output_table = length_output_table
        self.length_prod_table = length_prod_table
        self.result = result
        self.uniq_source_author = uniq_source_author
        self.rate_of_label = rate_of_label
        self.run_time = run_time
        self.check_point = check_point
        self.error_message = error_message

    def __repr__(self):
        return f"State({self.task_id}, {self.stat}, {self.prod_stat}, {self.model_type}, {self.predict_type}, " \
               f"{self.date_range}, {self.target_schema}, {self.create_time}, {self.peak_memory}, {self.length_receive_table}," \
               f"{self.length_output_table}, {self.length_prod_table}, {self.result}, {self.uniq_source_author}, " \
               f"{self.rate_of_label}, {self.run_time}, {self.check_point}, {self.error_message})"


class ModelStatus(Base):
    __tablename__ = TableName.model_status
    task_id = Column(String(32), primary_key=True)
    model_name = Column(String(100))
    training_status = Column(String(32))
    ext_status = Column(String(32))
    feature = Column(String(32), nullable=False)
    model_path = Column(String(100))
    error_message = Column(LONGTEXT)
    create_time = Column(DateTime, nullable=False)
    job_id = Column(Integer)
    # one-to-many collection
    report = relationship(
        "ModelReport",
        backref="model_status",
        cascade="all, delete",
        passive_deletes=True
    )
    term_weight = relationship(
        "TermWeights",
        backref="model_status",
        cascade="all, delete",
        passive_deletes=True
    )
    rules = relationship(
        "Rules",
        backref="model_status",
        cascade="all, delete",
        passive_deletes=True
    )
    upload_model = relationship(
        "UploadModel",
        backref="model_status",
        cascade="all, delete",
        passive_deletes=True
    )

    def __init__(self, task_id, model_name, training_status,
                 ext_status, feature, model_path,
                 error_message, create_time, job_id):
        self.task_id = task_id
        self.model_name = model_name
        self.training_status = training_status
        self.ext_status = ext_status
        self.feature = feature
        self.model_path = model_path
        self.error_message = error_message
        self.create_time = create_time
        self.job_id = job_id

    def __repr__(self):
        return f"ModelStatus({self.task_id}, {self.model_name}, {self.training_status}, " \
               f"{self.ext_status}, {self.feature}, {self.model_path}, {self.error_message}, " \
               f"{self.create_time}, {self.job_id})"


class ModelReport(Base):
    __tablename__ = TableName.model_report
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
    __tablename__ = TableName.term_weights
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


class Rules(Base):
    __tablename__ = TableName.rules
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(200), nullable=False)
    rule_type = Column(String(20), nullable=False)
    score = Column(DOUBLE, nullable=False)
    label = Column(String(100), nullable=False)
    match_type = Column(String(20), nullable=False)
    task_id = Column(String(32), ForeignKey('model_status.task_id', ondelete="CASCADE"))

    def __init__(self, content, rule_type, score, label, match_type, task_id):
        self.content = content
        self.rule_type = rule_type
        self.score = score
        self.label = label
        self.match_type = match_type
        self.task_id = task_id

    def __repr__(self):
        return f"Rules({self.content}, {self.rule_type}, {self.score}, " \
               f"{self.label}, {self.match_type}, {self.task_id})"


class UploadModel(Base):
    __tablename__ = TableName.upload_model
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(100))
    status = Column(String(32))
    create_time = Column(DateTime, default=datetime.now())
    error_message = Column(LONGTEXT)
    upload_job_id = Column(Integer, unique=True)
    task_id = Column(String(32), ForeignKey('model_status.task_id', ondelete="CASCADE"))

    def __init__(self, file, status, create_time, task_id):
        self.file = file
        self.status = status
        self.create_time = create_time
        self.task_id = task_id

    def __repr__(self):
        return f"UploadModel({self.file}, {self.status}, {self.create_time}, {self.task_id})"


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

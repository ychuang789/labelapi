from datetime import datetime

from sqlalchemy import DateTime, Column, String, Integer, ForeignKey, Float, TEXT
from sqlalchemy.dialects.mysql import LONGTEXT, DOUBLE
from sqlalchemy.orm import declarative_base, relationship

from settings import TableName

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

    eval_details = relationship(
        "EvalDetails",
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
    eval_details = relationship(
        "EvalDetails",
        backref="model_report",
        cascade="all, delete",
        passive_deletes=True
    )

    def __init__(self, dataset_type, accuracy, report, create_time, task_id):
        self.dataset_type = dataset_type
        self.accuracy = accuracy
        self.report = report
        self.create_time = create_time
        self.task_id = task_id

    def __repr__(self):
        return f"ModelReport({self.dataset_type}, {self.accuracy}, {self.report}, " \
               f"{self.create_time}, {self.task_id})"


class EvalDetails(Base):
    __tablename__ = TableName.eval_details
    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer)
    content = Column(LONGTEXT)
    ground_truth = Column(String(100))
    predict_label = Column(String(100))
    report_id = Column(Integer, ForeignKey('model_report.id', ondelete="CASCADE"))
    task_id = Column(String(32), ForeignKey('model_status.task_id', ondelete="CASCADE"))

    def __init__(self, doc_id, content, ground_truth, predict_label, report_id, task_id):
        self.doc_id = doc_id
        self.content = content
        self.ground_truth = ground_truth
        self.predict_label = predict_label
        self.report_id = report_id
        self.task_id = task_id

    def __repr__(self):
        return f"EvalDetails({self.task_id}:{self.doc_id}, {self.content}, " \
               f"{self.ground_truth}, {self.predict_label})"


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


class FilterRuleTask(Base):
    __tablename__ = TableName.filter_rule_task
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(32))
    create_time = Column(DateTime, nullable=False)
    feature = Column(String(32), nullable=False)
    model_name = Column(String(100), nullable=False)
    error_message = Column(LONGTEXT, nullable=True)
    filter_rule = relationship(
        "FilterRules",
        backref="filter_rule_task",
        cascade="all, delete",
        passive_deletes=True)

    def __int__(self, label, create_time, feature, model_name, error_message):
        self.label = label
        self.create_time = create_time
        self.feature = feature
        self.model_name = model_name
        self.error_message = error_message

    def __repr__(self):
        return f"FilterRuleTask({self.label}, {self.create_time}, {self.feature}, {self.model_name})"


class FilterRules(Base):
    __tablename__ = TableName.filter_rule
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(200), nullable=False)
    rule_type = Column(String(20), nullable=False)
    label = Column(String(100), nullable=False)
    match_type = Column(String(20), nullable=False)
    task_id = Column(Integer, ForeignKey('filter_rule_task.task_id', ondelete="CASCADE"))

    def __init__(self, content, rule_type, label, match_type, task_id):
        self.content = content
        self.rule_type = rule_type
        self.label = label
        self.match_type = match_type
        self.task_id = task_id

    def __repr__(self):
        return f"FilterRules({self.content}, {self.rule_type}, " \
               f"{self.label}, {self.match_type}, {self.task_id})"

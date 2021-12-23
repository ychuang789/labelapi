import pymysql
from retry import retry
from sqlalchemy import create_engine, DateTime, Table, Column, String, MetaData, inspect, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT, DOUBLE

from settings import DatabaseConfig

def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]
    return inner

@singleton
class DBConnector(object):

    def __init__(self, ):
        self.conn = None

    @retry(tries=5, delay=2)
    def create_connection(self, **kwargs):
        """create connection"""
        return pymysql.connect(**kwargs)

    def __enter__(self):
        self.conn = self.create_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

class DBConnection(object):
    connection = None

    @classmethod
    def get_connection(cls, new=False, **kwargs):
        if new or not cls.connection:
            cls.connection = DBConnector().create_connection(**kwargs)
        return cls.connection

    @classmethod
    def execute_query(cls, query: str, single=False, alter=False, **kwargs):
        connection = cls.get_connection(**kwargs)
        cursor = connection.cursor()
        cursor.execute(query)
        if not alter:
            if single:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            cursor.close()
            return result
        else:
            cursor.close()
            return None

class ConnectionConfigGenerator:

    @staticmethod
    def xingyi_database(schema='wh_backpackers',
                        host=DatabaseConfig.INPUT_HOST,
                        port=DatabaseConfig.INPUT_PORT,
                        user=DatabaseConfig.INPUT_USER,
                        password=DatabaseConfig.INPUT_PASSWORD,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor):
        """return xingyi database connection config dict"""
        return {'host': host,
                'port': port,
                'user': user,
                'password': password,
                'db': schema,
                'charset': charset,
                'cursorclass': cursorclass}

    @staticmethod
    def rd2_database(schema='audience_result',
                     host=DatabaseConfig.OUTPUT_HOST,
                     port=DatabaseConfig.OUTPUT_PORT,
                     user=DatabaseConfig.OUTPUT_USER,
                     password=DatabaseConfig.OUTPUT_PASSWORD,
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor):
        """return rd2 database connection config dict"""
        return {'host': host,
                'port': port,
                'user': user,
                'password': password,
                'db': schema,
                'charset': charset,
                'cursorclass': cursorclass}

    @staticmethod
    def other_database(schema=None, host=None, port=None, user=None, password=None,
                       charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor):
        """return connection of outer database config dict"""
        return {'host': host,
                'port': port,
                'user': user,
                'password': password,
                'db': schema,
                'charset': charset,
                'cursorclass': cursorclass}


class QueryManager:
    state_query = f"""select * from state"""
    model_dataset = f"""SELECT d.id, d.s_area_id, d.author, d.title, d.content, d.post_time, l.name as label
                        FROM `audience-toolkit-django`.labeling_jobs_document d
                        INNER JOIN `audience-toolkit-django`.labeling_jobs_label l USING(labeling_job_id)
                        WHERE d.labeling_job_id = 1;"""


def create_modeling_status_table():
    try:
        engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=True)
    except Exception as e:
        raise f'connection failed, additional error message {e}'

    inspector = inspect(engine)
    if 'modeling_status' in inspector.get_table_names():
        return

    meta = MetaData()
    modeling_status = Table(
        'modeling_status', meta,
        Column('task_id', String(32), primary_key=True),
        Column('model_name', String(100)),
        Column('training_status', String(32)),
        Column('ext_predict_status', String(32)),
        Column('feature', String(32), nullable=False),
        Column('model_path', String(100)),
        Column('error_message', LONGTEXT),
        Column('create_time', DateTime, nullable=False)
    )
    meta.create_all(engine)
    engine.dispose()

def create_modeling_report_table():
    try:
        engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, echo=True)
    except Exception as e:
        raise f'connection failed, additional error message {e}'

    inspector = inspect(engine)
    if 'modeling_report' in inspector.get_table_names():
        return

    meta = MetaData()
    modeling_report = Table(
        'modeling_report', meta,
        Column('task_id', String(32), ForeignKey("modeling_status.task_id"), nullable=False),
        Column('dataset_type', String(10)),
        Column('accuracy', DOUBLE, nullable=False),
        Column('report', String(1000), nullable=False),
        Column('create_time', DateTime, nullable=False)
    )
    meta.create_all(engine)
    engine.dispose()

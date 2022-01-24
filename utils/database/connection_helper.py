from typing import Dict, List

import pymysql
from retry import retry
from sqlalchemy import create_engine, DateTime, Table, Column, String, MetaData, Integer, inspect, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT, DOUBLE
from sqlalchemy.orm import declarative_base, relationship

from settings import DatabaseConfig, TestDatabaseConfig


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


# @singleton
class DBConnector(object):

    def __init__(self, conn=None):
        self.conn = conn

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
    def execute_query(cls, query: str, alter=False, single=False, **kwargs):
        connection = cls.get_connection(**kwargs)
        cursor = connection.cursor()
        cursor.execute(query)
        if alter:
            connection.commit()
            cursor.close()
        else:
            if single:
                result = None if alter else cursor.fetchone()
            else:
                result = None if alter else cursor.fetchall()
            cursor.close()
            return result


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
    def test_database(schema='audience-toolkit-django',
                      host=TestDatabaseConfig.HOST,
                      port=TestDatabaseConfig.PORT,
                      user=TestDatabaseConfig.USER,
                      password=TestDatabaseConfig.PASSWORD,
                      charset='utf8mb4',
                      cursorclass=pymysql.cursors.DictCursor):
        """This one is only for data scrapping from the django site when testing the service at localhost"""
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

    @staticmethod
    def get_state_query(**kwargs):
        if task_id := kwargs.get('task_id'):
            return f"""select * from state where task_id = '{task_id}'"""

        else:
            return f"""select * from state"""

    @staticmethod
    def get_model_query(**kwargs):
        if get_data := kwargs.get('labeling_job_id'):
            if document_type := kwargs.get('document_type'):
                return f"""SELECT *
                           FROM `audience-toolkit-django`.labeling_jobs_document d
                           INNER JOIN `audience-toolkit-django`.labeling_jobs_label l USING(labeling_job_id)
                           WHERE d.labeling_job_id = {get_data} and d.document_type = '{document_type}'"""
            else:
                return f"""SELECT *
                           FROM `audience-toolkit-django`.labeling_jobs_document d
                           INNER JOIN `audience-toolkit-django`.labeling_jobs_label l USING(labeling_job_id)
                           WHERE d.labeling_job_id = {get_data}'"""

        if kwargs.get('model_job_id') and not kwargs.get('model_report'):
            return f"""select * from model_status where job_id = {kwargs.get('model_job_id')}"""

        if kwargs.get('model_job_id') and kwargs.get('model_report'):
            return f"""select * from model_report where job_id = {kwargs.get('model_job_id')}"""

    @staticmethod
    def get_model_job_id(job_id: int):
        if job_id:
            return f"""SELECT model_name, model_path FROM model_status WHERE job_id = {job_id};"""

    @staticmethod
    def get_model_job_ids(job_ids: List[int]):
        """ sort by the same order with job_ids"""
        return f"""SELECT * 
                    FROM audience_result.model_status
                    WHERE job_id in {tuple(job_ids)}
                    ORDER BY FIND_IN_SET(job_id, '{','.join([str(i) for i in job_ids])}');"""

    @staticmethod
    def get_rule_query(labeling_job_id: int):
        return f"""SELECT * 
                    FROM `audience-toolkit-django`.labeling_jobs_rule r 
                    INNER JOIN `audience-toolkit-django`.labeling_jobs_label l USING(labeling_job_id)
                    WHERE r.labeling_job_id = {labeling_job_id}"""

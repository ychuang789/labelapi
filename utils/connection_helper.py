import pymysql
from retry import retry

from settings import DatabaseConfig


class DBConnector(object):
    def __init__(self, **kwargs):
        self.conn_config = kwargs
        self.conn = None

    @retry(tries=5, delay=2)
    def create_connection(self):
        """create connection"""
        return pymysql.connect(**self.conn_config)

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
            cls.connection = DBConnector(**kwargs).create_connection()
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





import pymysql
from retry import retry

class DBConnector():

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






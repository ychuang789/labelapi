from typing import List
from unittest import TestCase

import pymysql

from settings import DatabaseConfig
from utils.connection_helper import DBConnection


class TestConnection(TestCase):
    config = {'host': DatabaseConfig.OUTPUT_HOST,
              'port': DatabaseConfig.OUTPUT_PORT,
              'user': DatabaseConfig.OUTPUT_USER,
              'password': DatabaseConfig.OUTPUT_PASSWORD,
              'cursorclass': pymysql.cursors.DictCursor,
              'db': 'audience_result',
              'charset': 'utf8mb4',
              }

    def test_single_response(self):
        task_id = 'cb87c23662f911ecb688d45d6456a14d'
        query = f"""select * from state where task_id = '{task_id}';"""
        result = DBConnection.execute_query(query=query, single=True, **self.config)
        self.assertEqual(task_id, result['task_id'])

    def test_multi_response(self):
        query = """select * from state where create_time > '2021-12-20 00:00:00' and create_time < '2021-12-22 00:00:00'"""
        result = DBConnection.execute_query(query=query, **self.config)
        self.assertIsInstance(result, List)




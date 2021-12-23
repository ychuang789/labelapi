from typing import List, Dict
from unittest import TestCase

import pymysql

from settings import DatabaseConfig
from utils.connection_helper import DBConnection, ConnectionConfigGenerator, QueryManager


class TestConnection(TestCase):

    def test_connection_config_generator(self):
        self.assertIsInstance(ConnectionConfigGenerator.other_database(), Dict)
        self.assertIsNotNone(ConnectionConfigGenerator.rd2_database().get('host'))
        self.assertIsNotNone(ConnectionConfigGenerator.xingyi_database().get('host'))

    def test_single_response(self):
        task_id = 'cb87c23662f911ecb688d45d6456a14d'
        query = QueryManager.state_query + f""" where task_id = '{task_id}';"""
        result = DBConnection.execute_query(query=query, single=True,
                                            **ConnectionConfigGenerator.rd2_database(schema="audience_result"))
        self.assertEqual(task_id, result['task_id'])

    def test_multi_response(self):
        query = QueryManager.state_query + " where create_time > '2021-12-20 00:00:00' and create_time < '2021-12-22 00:00:00'"
        result = DBConnection.execute_query(query=query,
                                            **ConnectionConfigGenerator.rd2_database(schema="audience_result"))
        self.assertIsInstance(result, List)




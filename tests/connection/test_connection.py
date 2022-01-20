from typing import List, Dict
from unittest import TestCase

from utils.database.connection_helper import DBConnection, ConnectionConfigGenerator, QueryManager


class TestConnection(TestCase):

    def test_connection_config_generator(self):
        self.assertIsInstance(ConnectionConfigGenerator.other_database(), Dict)
        self.assertIsNotNone(ConnectionConfigGenerator.rd2_database().get('host'))
        self.assertIsNotNone(ConnectionConfigGenerator.xingyi_database().get('host'))

    def test_single_response(self):
        kw = {'task_id' : 'cb87c23662f911ecb688d45d6456a14d'}
        query = QueryManager.get_state_query(**kw)
        result = DBConnection.execute_query(query=query, single=True,
                                            **ConnectionConfigGenerator.rd2_database(schema="audience_result"))
        self.assertEqual(kw['task_id'], result['task_id'])




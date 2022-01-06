from unittest import TestCase
from dump.groups.dump_core import DumpWorker
from settings import DatabaseConfig


class TestDumpWorker(TestCase):
    """ Use 2021 gender data as Testcase"""

    id_list = [14,15,16,17,18,20]
    old_table_database = DatabaseConfig.DUMP_FROM_SCHEMA
    new_table_database = DatabaseConfig.OUTPUT_SCHEMA
    dump_database = DatabaseConfig.DUMP_TO_SCHEMA
    verbose = True

    def setUp(self):
        self.model = DumpWorker(id_list=self.id_list,
                                old_table_database=self.old_table_database,
                                new_table_database=self.new_table_database,
                                dump_database=self.dump_database,
                                verbose=self.verbose)

    def test_merge(self):
        table_result = self.model.run_merge()
        self.assertIsNotNone(table_result)




from dump.groups.gender_dump import GenderDump
from dump.groups.marriage_dump import MarriageDump
from settings import DatabaseConfig

class DumpFlow:
    @staticmethod
    def generate_dump_flow(group_property, task_ids, year,
                           input_database=DatabaseConfig.DUMP_FROM_SCHEMA,
                           output_database=DatabaseConfig.OUTPUT_SCHEMA):
        if group_property == 'GENDER':
            return GenderDump(task_ids, input_database, output_database, previous_year=year)
        if group_property == 'MARRIAGE':
            return MarriageDump(task_ids, input_database, output_database, previous_year=year)

        return None






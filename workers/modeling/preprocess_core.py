from utils.database.connection_helper import DBConnection, ConnectionConfigGenerator, QueryManager
from utils.data.data_helper import DataNotFoundError, load_examples
from utils.enum_config import DatasetType

class PreprocessWorker:

    def __str__(self):
        return f"the class for data preprocessing"

    @staticmethod
    def run_processing(dataset_number, dataset_schema,
                       sample_count=1000, is_train=True):
        if is_train:
            data_dict = {}
            for i in [t.value for t in DatasetType]:
                if i == DatasetType.EXT_TEST.value:
                    continue
                condition = {'labeling_job_id': dataset_number, 'document_type': i}
                data = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                                  **ConnectionConfigGenerator.rd2_database(schema=dataset_schema))
                if not data:
                    raise DataNotFoundError('There are missing data from database')
                data = load_examples(data=data, sample_count=sample_count)
                data_dict.update({i: data})
            return data_dict
        else:
            condition = {'labeling_job_id': dataset_number, 'document_type': DatasetType.EXT_TEST.value}
            data = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                              **ConnectionConfigGenerator.rd2_database(schema=dataset_schema))
            if not data:
                raise DataNotFoundError('There are missing data from database')
            data = load_examples(data=data, sample_count=sample_count)
        return data

from typing import List, Dict

from settings import DATA_FILTER_TASK_ID_LIST
from utils.data.input_example import InputExample
from workers.preprocessing.data_filter_core import DataFilterWorker


class DataFilterBuilder:

    # @staticmethod
    # def get_task_instance(id_list: List[int]):
    #     return [DataFilterWorker(filter_task_id=i) for i in id_list]

    @staticmethod
    def data_filter_method_chain(start: List[InputExample], id_list: List[int]):
        worker_list = [DataFilterWorker(filter_task_id=i) for i in id_list]
        temp_result = start
        for worker in worker_list:
            if not hasattr(worker, 'run_task'):
                raise ValueError('Instance should contain run_task method')
            temp_result = worker.run_task(temp_result)
        return temp_result


def model_dataset_cleaning(dataset_dict, data_filter_id: List[int] = None) -> Dict[str, List[InputExample]]:
    data_filter_id = data_filter_id if data_filter_id else DATA_FILTER_TASK_ID_LIST
    if not data_filter_id:
        return dataset_dict

    clean_dict = {}
    for dataset_type, input_dataset_list in dataset_dict.items():
        clean_dataset = DataFilterBuilder.data_filter_method_chain(start=input_dataset_list, id_list=data_filter_id)
        clean_dict.update({
            dataset_type: clean_dataset
        })
    return clean_dict


def input_examples_convert(fetch_dict_list: List[dict]) -> List[InputExample]:
    output_list = []
    for fetch_dict in fetch_dict_list:
        output_list.append(
            InputExample(
                id_=fetch_dict.get('id'),
                s_area_id=fetch_dict.get('s_area_id'),
                author=fetch_dict.get('author'),
                title=fetch_dict.get('title'),
                content=fetch_dict.get('content'),
                post_time=fetch_dict.get('post_time'))
        )

    return output_list


def execute_data_filter(dataset: List[dict], data_filter_id: List[int] = None):
    data_filter_id = data_filter_id if data_filter_id else DATA_FILTER_TASK_ID_LIST
    if not data_filter_id:
        return dataset

    clean_dataset = DataFilterBuilder.data_filter_method_chain(start=input_examples_convert(dataset),
                                                               id_list=data_filter_id)
    output_list = []
    for data in clean_dataset:
        temp_dict = data.__dict__
        temp_dict.pop('label')
        output_list.append(temp_dict)

    return output_list

import csv
import os
from typing import List

from definition import SAVE_DETAIL_FOLDER
from settings import SAVE_DETAIL_EXTENSION


def list_dict_to_csv(dataset: List[dict], filename: str):
    filepath = pre_check(filename)
    write_file(dataset, filepath)

    return filepath


def pre_check(filename: str):
    filename = filename if check_extension(filename) else filename + '.csv'
    filepath = os.path.join(SAVE_DETAIL_FOLDER, filename)

    if check_file_exist(filepath):
        truncate_file(filepath)

    return filepath


def check_extension(filename: str):
    temp_filename = filename.rsplit(sep='.', maxsplit=1)
    if temp_filename[-1] not in SAVE_DETAIL_EXTENSION:
        return False
    else:
        return True


def check_file_exist(filepath: str):
    if os.path.isfile(filepath):
        return True
    else:
        return False


def truncate_file(filepath: str):
    try:
        with open(filepath, 'w+') as f:
            f.truncate()
    except Exception as e:
        raise e


def write_file(dataset: List[dict], filepath: str):
    try:
        with open(filepath, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=list(dataset[0].keys()))
            writer.writeheader()
            for d in dataset:
                writer.writerow(d)
    except Exception as e:
        raise e


def find_file(report_id: int):
    for root, dirs, files in os.walk(SAVE_DETAIL_FOLDER):
        for file in files:
            if file.startswith(f'{report_id}'):
                return file, os.path.join(root, file)

    return None

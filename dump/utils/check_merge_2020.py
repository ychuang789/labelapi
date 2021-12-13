import os
from collections import defaultdict
from datetime import datetime

import duplicate as duplicate
from tqdm import tqdm
from typing import List, Dict

import pandas as pd
from sqlalchemy import create_engine

from settings import DatabaseConfig
from utils.database_core import connect_database, to_dataframe
from utils.helper import get_logger

CONFLICT_GROUPS = ('/male', '/female')

_logger = get_logger('fix_2020')

def get_data(schema, query, output=True):
    connection = connect_database(schema=schema, output=output)
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    return result

def get_old_table_list(schema, year):
    q = f"""
    SHOW TABLES 
    FROM {schema} 
    WHERE Tables_in_{schema} 
    LIKE 'wh_panel_mapping_%' AND
    Tables_in_{schema} LIKE '%{year}' 
    """
    result = get_data(schema, q, output=False)
    return [v for d in result for k,v in d.items()]

def get_old_data(schema, table_name):
    q = f"""
    SELECT source_author, panel, create_time 
    FROM {table_name} 
    """
    result = to_dataframe(get_data(schema, q, output=False))
    return result

def get_current_data(schema, table_name):
    q = f"""
    SELECT source_author, panel 
    FROM {table_name} 
    """
    result = to_dataframe(get_data(schema, q, output=True))
    return result

def create_new_table(table_name: str, schema=None):
    insert_sql = f'CREATE TABLE IF NOT EXISTS `{table_name}`(' \
                 f'`source_author` TEXT NOT NULL,' \
                 f'`panel` VARCHAR(200) NOT NULL,' \
                 f'`create_time` DATETIME NOT NULL'\
                 f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                 f'AUTO_INCREMENT=1 ;'
    connection = connect_database(schema=schema, output=True)
    cursor = connection.cursor()
    try:
        cursor.execute(insert_sql)
        connection.close()
    except Exception as e:
        raise e

def write_into_table(df, schema, table_name):
    create_new_table(table_name, schema=schema)
    connection = create_engine(f'mysql+pymysql://{os.getenv("OUTPUT_USER")}:' \
                              f'{os.getenv("OUTPUT_PASSWORD")}@{os.getenv("OUTPUT_HOST")}:' \
                              f'{os.getenv("OUTPUT_PORT")}/{schema}?charset=utf8mb4').connect()
    df.to_sql(name=table_name, con=connection, if_exists='append', index=False)
    connection.close()

def merge_data(old_data, _current_data, now = datetime.now()):
    old_data['source_author'] = old_data['source_author'].str.strip()
    _current_data['source_author'] = _current_data['source_author'].str.strip()
    current_data = _current_data.drop_duplicates(subset=['source_author', 'panel'], keep='last')

    old_data_gender = old_data[old_data['panel'].isin(CONFLICT_GROUPS)]
    old_data_other = old_data[~old_data['panel'].isin(CONFLICT_GROUPS)]

    old_overlap_data = old_data_gender[old_data_gender['source_author'].isin(current_data['source_author'].values.tolist())]
    new_overlap_data = current_data[current_data['source_author'].isin(old_data_gender['source_author'].values.tolist())]
    new_no_overlap_data = current_data[~current_data['source_author'].isin(old_data_gender['source_author'].values.tolist())]

    overlap_data = old_overlap_data.merge(new_overlap_data, left_on=('source_author'), right_on=('source_author'),suffixes=('_old','_new'))
    _logger.info(f'sum of nan in merge {overlap_data.isna().sum()}')

    new_data = pd.DataFrame(columns=['source_author', 'panel', 'create_time'])
    new_data = new_data.append(old_data_other)
    new_data = new_data.append(new_no_overlap_data)
    new_data = new_data.fillna(value={'create_time': now})
    _logger.info(f'sum of nan in new_data before conflict {new_data.isna().sum()}')

    result_list = []
    for idx, row in tqdm(overlap_data.iterrows()):
        if row.panel_old != row.panel_new:
            result_list.append(row.panel_new)
            row.create_time = now
        else:
            result_list.append(row.panel_old)

    result_df = pd.DataFrame({'panel':result_list})

    temp = pd.concat([overlap_data.reset_index(drop=True), result_df.reset_index(drop=True)], axis=1)

    result_overlap_df = temp[['source_author','panel','create_time']]
    new_data = new_data.append(result_overlap_df)
    _logger.info(f'sum of nan in new_data after concat conflict {new_data.isna().sum()}')


    return new_data

def check_merge_data(**kwargs):
    old_data_db = kwargs.get('old_data_db')
    # new_data_db = kwargs.get('new_data_db')
    year = kwargs.get('previous_year')

    return get_old_table_list(old_data_db, year)

def checker(df):
    # df = get_current_data(schema, table_name)
    duplicate = df[df.duplicated(subset=['source_author', 'panel'])]

    check_dict = defaultdict(list)
    for idx, row in tqdm(df.iterrows()):
        if row.panel in CONFLICT_GROUPS:
            check_dict[row.source_author].append(row.panel)

    return len(duplicate), dict(check_dict)

def run_task(**kwargs):
    old_data_db = kwargs.get('old_data_db')
    new_data_db = kwargs.get('new_data_db')

    old_table_list = check_merge_data(**kwargs)

    for i in old_table_list:
        _logger.info(f'get {kwargs.get("previous_year")} data...')
        old_df = get_old_data(old_data_db, i)

        _logger.info(f'get current data...')
        target_table_name = i.rsplit('_', 1)[0]
        new_df = get_current_data(new_data_db, target_table_name)

        _logger.info('start checking conflict...')
        new_data = merge_data(old_df, new_df)

        duplicate_row_number, dict_checker = checker(new_data)

        if duplicate_row_number > 0:
            _logger.error(f'table conflict result {i} contains duplicate row number {duplicate_row_number}')

        for k,v in dict_checker.items():
            if len(v) > 1:
                _logger.error(f'table conflict result {i} contains conflict on source_author {k}')


        _logger.info('start writing data into new table...')
        temp_table_name = target_table_name + '_check'
        create_new_table(temp_table_name, new_data_db)
        write_into_table(new_data, new_data_db, temp_table_name)




def clean_rest(schema, tb_list, now = datetime.now()):
    new_data_db = schema
    for i in tb_list:
        _logger.info(f'get current data...')
        df = get_current_data(schema, i)
        df['source_author'] = df['source_author'].str.strip()
        df = df.drop_duplicates(subset=['source_author', 'panel'], keep='last')

        create_time = [now] * len(df)
        temp = pd.DataFrame({'create_time': create_time})
        _logger.info(f'concating...')
        df = pd.concat([df.reset_index(drop=True), temp], axis=1)
        duplicate_row_number, dict_checker = checker(df)

        if duplicate_row_number > 0:
            _logger.error(f'table conflict result {i} contains duplicate row number {duplicate_row_number}')

        for k, v in dict_checker.items():
            if len(v) > 1:
                _logger.error(f'table conflict result {i} contains conflict on source_author {k}')
                print(f'{k}:{v}')

        _logger.info(f'writing into table...')

        temp_table_name = i + '_check'
        create_new_table(temp_table_name, new_data_db)
        write_into_table(df, new_data_db, temp_table_name)


# ====

def get_generate_dict_from_state(task_ids: List[str], schema=DatabaseConfig.OUTPUT_SCHEMA):
    condition = '","'.join(task_ids)
    query = f"""
    select *
    from state 
    where task_id in ("{condition}")
    """
    return get_data(schema, query, output=True)





























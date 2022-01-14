import os
from datetime import datetime
from typing import List

from sqlalchemy import create_engine

import pandas as pd

from definition import AUDIENCE_PRODUCTION_PATH
from settings import CONFLICT_GROUPS, DatabaseConfig, TABLE_PREFIX, TABLE_GROUPS_FOR_INDEX, DUMP_COLUMNS
from utils.database.database_helper import connect_database, to_dataframe
from utils.exception_manager import OutputZIPNotFoundError
from utils.general_helper import get_logger

def get_table_suffix_condition() -> str:
    temp = '|'.join(TABLE_GROUPS_FOR_INDEX.keys())
    condition = '(' + temp + ')$'
    return condition

def get_data(schema, query, output=True):
    connection = connect_database(schema=schema, output=output)
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        raise e
    finally:
        connection.close()

def get_old_table_list(schema, condition):
    q = f"""
    SHOW TABLES 
    FROM {schema} 
    WHERE Tables_in_{schema} 
    LIKE '{TABLE_PREFIX}%' AND
    Tables_in_{schema} REGEXP '{condition}' 
    """
    result = get_data(schema, q, output=False)
    return [v for d in result for k, v in d.items()]

def get_old_data(schema, table_name):
    q = f"""
    SELECT source_author, panel, create_time 
    FROM {table_name} 
    """
    result = to_dataframe(get_data(schema, q, output=False))
    return result

def get_current_data(schema, table_name, task_id):
    q = f"""
    SELECT source_author, panel 
    FROM {table_name} 
    WHERE task_id = '{task_id}'
    """
    result = to_dataframe(get_data(schema, q, output=True))
    return result

def get_dump_table_list(schema):
    q = f"""SELECT table_name FROM information_schema.tables
            WHERE table_schema = '{schema}';"""
    return get_data(schema, q)

def get_generate_dict_from_state(task_ids: List[str], schema=DatabaseConfig.OUTPUT_SCHEMA):
    condition = '","'.join(task_ids)
    query = f"""
    select *
    from state 
    where task_id in ("{condition}")
    """
    return get_data(schema, query, output=True)

def get_dump_table_ids(schema, condition: List[int]):

    q = f"""SELECT t.task_id 
            FROM `audience-toolkit-django`.predicting_jobs_predictingtarget t
            LEFT JOIN `audience-toolkit-django`.predicting_jobs_predictingjob p USING(id)
            WHERE t.predicting_job_id in {tuple(condition)};"""

    return get_data(schema, q)


def create_new_table(table_name: str, schema=None):
    insert_sql = f'CREATE TABLE IF NOT EXISTS `{table_name}`(' \
                 f'`source_author` TEXT NOT NULL,' \
                 f'`panel` VARCHAR(200) NOT NULL,' \
                 f'`create_time` DATETIME NOT NULL'\
                 f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                 f'AUTO_INCREMENT=1 ;'
    connection = connect_database(schema=schema, output=True)
    try:
        cursor = connection.cursor()
        cursor.execute(insert_sql)
    except Exception as e:
        raise e
    finally:
        connection.close()

def truncate_table(table_name: str, schema=None):
    query = f"""TRUNCATE TABLE {table_name}"""
    connection = connect_database(schema=schema, output=True)
    try:
        cursor = connection.cursor()
        cursor.execute(query)
    except Exception as e:
        raise e
    finally:
        connection.close()

def write_into_table(df, schema, table_name):
    # create_new_table(table_name, schema=schema)
    connection = create_engine(f'mysql+pymysql://{os.getenv("OUTPUT_USER")}:' \
                              f'{os.getenv("OUTPUT_PASSWORD")}@{os.getenv("OUTPUT_HOST")}:' \
                              f'{os.getenv("OUTPUT_PORT")}/{schema}?charset=utf8mb4').connect()
    df.to_sql(name=table_name, con=connection, if_exists='append', index=False)
    connection.close()

def check_merge_data(**kwargs):
    old_data_db = kwargs.get('old_data_db')
    # new_data_db = kwargs.get('new_data_db')
    year = kwargs.get('previous_year')

    return get_old_table_list(old_data_db, year)


def merge_data(old_data: pd.DataFrame, _current_data: pd.DataFrame,
               logger: get_logger, now: datetime = datetime.now()):

    logger.info("start merging data...")

    old_data['source_author'] = old_data['source_author'].str.strip()
    _current_data['source_author'] = _current_data['source_author'].str.strip()
    current_data = _current_data.drop_duplicates(subset=['source_author', 'panel'], keep='last')

    conflict_list = [i for v in CONFLICT_GROUPS.values() for i in v]

    old_data_conflict = old_data[old_data['panel'].isin(conflict_list)]
    old_data_non_conflict = old_data[~old_data['panel'].isin(conflict_list)]
    new_data_conflict = current_data[current_data['panel'].isin(conflict_list)]
    new_data_non_conflict = current_data[~current_data['panel'].isin(conflict_list)]

    # merge the non conflict data
    output = pd.DataFrame(columns=DUMP_COLUMNS)
    output = output.append(old_data_non_conflict)
    output = output.append(new_data_non_conflict)
    output = output.drop_duplicates(subset=['source_author', 'panel'], keep='last')

    for k, v in CONFLICT_GROUPS.items():
        logger.info(f'{k} group')
        _old_data = old_data_conflict[old_data_conflict['panel'].isin(v)]
        _new_data = new_data_conflict[new_data_conflict['panel'].isin(v)]

        if _new_data.empty:
            logger.info(f'no {k} data in new dataset, directly append old dataset into output')
            output.append(_old_data)
            continue

        old_overlap_data = _old_data[
            _old_data['source_author'].isin(_new_data['source_author'].values.tolist())]
        old_no_overlap_data = _old_data[~
            _old_data['source_author'].isin(_new_data['source_author'].values.tolist())]
        new_overlap_data = _new_data[
            _new_data['source_author'].isin(_old_data['source_author'].values.tolist())]
        new_no_overlap_data = _new_data[
            ~_new_data['source_author'].isin(_old_data['source_author'].values.tolist())]

        # merge the non overlap data
        output = output.append(old_no_overlap_data)
        output = output.append(new_no_overlap_data)
        output = output.fillna(value={'create_time': now})
        logger.debug(f'sum of nan in output df before dealing conflict is {output.isna().sum()}')
        if output.isnull().values.any():
            raise ValueError('output data should not contain any nan value')

        if old_overlap_data.empty:
            logger.info(f'there is no overlap data of conflict group')
            continue

        assert len(old_overlap_data) == len(new_overlap_data), 'overlap conflict data should have same number of rows'

        _overlap = old_overlap_data.merge(new_overlap_data, left_on=('source_author'),
                                   right_on=('source_author'),
                                   suffixes=('_old', '_new'))

        logger.debug(f'{k} group sum of nan in merge {_overlap.isna().sum()}')
        if output.isnull().values.any():
            raise ValueError(f'overlap data in {k} group should not contain any nan value')

        result_list = []
        time_list = []
        for idx, row in _overlap.iterrows():
            if row.panel_old != row.panel_new:
                result_list.append(row.panel_new)
                time_list.append(now)
            else:
                result_list.append(row.panel_old)
                time_list.append(row.create_time_old)

        _overlap['create_time'] = time_list
        result_df = pd.DataFrame({'panel': result_list})
        temp = pd.concat([_overlap.reset_index(drop=True), result_df.reset_index(drop=True)], axis=1)
        result_overlap_df = temp[['source_author', 'panel', 'create_time']]
        output = output.append(result_overlap_df)

    logger.debug(f'sum of nan in output df after concat conflict data {output.isna().sum()}')
    if output.isnull().values.any():
        raise ValueError(f'overlap data should not contain any nan value')

    return output


def clean_rest(df: pd.DataFrame, now: datetime = datetime.now()):

    df['source_author'] = df['source_author'].str.strip()
    df = df.drop_duplicates(subset=['source_author', 'panel'], keep='last')

    create_time = [now] * len(df)
    temp = pd.DataFrame({'create_time': create_time})

    df = pd.concat([df.reset_index(drop=True), temp], axis=1)
    return df

def execute_zip_command(table_name: str,
                        production_path=AUDIENCE_PRODUCTION_PATH) -> None:
    host = DatabaseConfig.OUTPUT_HOST
    port = DatabaseConfig.OUTPUT_PORT
    user = DatabaseConfig.OUTPUT_USER
    password = DatabaseConfig.OUTPUT_PASSWORD
    schema = DatabaseConfig.OUTPUT_SCHEMA
    direction = datetime.now().strftime('%Y_%m_%d')
    base_path = f'{production_path}/{direction}_dump'

    check_path = base_path + '/'
    if not os.path.isdir(check_path):
        os.mkdir(check_path)

    command = f"""
    mysqldump -u{user} -p{password} -h{host} -P{port} 
    --lock-tables=false {schema} {table_name} | zip > {base_path}/{table_name}.zip
    """
    os.system(command)

    if not os.path.isfile(check_path + f'{table_name}.zip'):
        raise OutputZIPNotFoundError(f'table {table_name} writing to ZIP failed...')

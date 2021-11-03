import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pymysql
import pandas as pd
from sqlmodel import SQLModel, create_engine
from sqlalchemy import create_engine as C
from tqdm import tqdm

from definition import SCRAP_FOLDER, SAVE_FOLDER
from utils.helper import get_logger
from utils.selections import QueryStatements
from settings import DatabaseInfo, SOURCE, CreateLabelRequestBody


def create_db(db_path, config_db):
    if os.path.exists(f'../{db_path}'):
        pass
    else:
        engine = create_engine(f'{config_db}', encoding='utf-8')
        SQLModel.metadata.create_all(engine)

def connect_database(schema = None, output = False):
    if not output:
        config = {
            'host': DatabaseInfo.host,
            'port': DatabaseInfo.port,
            'user': DatabaseInfo.user,
            'password': DatabaseInfo.password,
            'db': schema,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
        }
    else:
        config = {
            'host': DatabaseInfo.output_host,
            'port': DatabaseInfo.output_port,
            'user': DatabaseInfo.output_user,
            'password': DatabaseInfo.output_password,
            'db': schema,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
        }
    try:
        connection = pymysql.connect(**config)
        return connection

    except:
        logging.error('Fail to connect to database.')


def to_dataframe(data):
    return pd.DataFrame.from_dict(data)


def scrap_data_to_csv(logger):
    func = connect_database
    file_list = []
    for query in QueryStatements:
        try:
            date_time = datetime.now().strftime("%Y%m%d%H%M%S")

            with func().cursor() as cursor:
                logger.info('connecting to database...')
                cursor.execute(query.value)
                result = to_dataframe(cursor.fetchall())
                print(len(result))
                logger.info('saving results...')
                result.to_csv(f"{SCRAP_FOLDER}/data_{str(query.name).lower()}_{date_time}.csv", encoding='utf-8-sig', index=None)
                logger.info(f'successfully saving file data_{str(query.name).lower()}_{date_time}.csv to {SCRAP_FOLDER}')
                file_list.append(f'data_{str(query.name).lower()}_{date_time}.csv')
                func().close()

        except:
            logger.error(f'fail to scrap data')
            return

    return file_list

def scrap_data_to_df(logger: get_logger, query: str, schema: str, _to_dict: bool = False):
    func = connect_database
    try:
        with func(schema=schema).cursor() as cursor:
            logger.info('connecting to database...')
            cursor.execute(query)
            if not _to_dict:
                result = to_dataframe(cursor.fetchall())
                func().close()
                return result
            else:
                result = cursor.fetchall()
                func().close()
                return result

    except Exception as e:
        logger.error(e)
        raise e

def get_count(enging_info, **kwargs):
    engine = C(enging_info).connect()

    if not kwargs.get('date_info'):
        # if not kwargs.get('chunk_by_source'):
        count = engine.execute(f"SELECT COUNT(*) FROM {kwargs.get('target_table')} "
                               f"WHERE {kwargs.get('predict_type')} IS NOT NULL").fetchone()[0]
        engine.close()
        return count

        # else:
        #     assert condition != None, f'chunk_by_source is set to True ' \
        #                               f'while source_array is not found.'
        #
        #     count = engine.execute(f"SELECT COUNT(*) FROM {kwargs.get('target_table')} "
        #                            f"WHERE s_id in {condition} "
        #                            f"AND {kwargs.get('predict_type')} IS NOT NULL").fetchone()[0]
        #     engine.close()
        #     return count
    else:
        # if not kwargs.get('chunk_by_source'):
        count = engine.execute(f"SELECT COUNT(*) "
                               f"FROM {kwargs.get('target_table')} "
                               f"WHERE {kwargs.get('predict_type')} IS NOT NULL " 
                               f"AND post_time BETWEEN '{kwargs.get('date_info_dict').get('start_time')}' "
                               f"AND '{kwargs.get('date_info_dict').get('end_time')}'"
                               ).fetchone()[0]
        engine.close()
        return count
        # else:
        #     assert condition != None, f'chunk_by_source is set to True ' \
        #                               f'while source_array is not found.'
        #
        #     count = engine.execute(f"SELECT COUNT(*) "
        #                            f"FROM {kwargs.get('target_table')} "
        #                            f"WHERE s_id in {condition} "
        #                            f"AND {kwargs.get('predict_type')} IS NOT NULL "
        #                            f"AND post_time >= '{kwargs.get('date_info_dict').get('start_time')}' "
        #                            f"AND post_time <= '{kwargs.get('date_info_dict').get('end_time')}'"
        #                            ).fetchone()[0]
        #     engine.close()
        #     return count

def get_label_data_count(task_id):
    connection = C(DatabaseInfo.output_engine_info).connect()
    q = f'SELECT length_output_table FROM state where task_id = "{task_id}";'
    _count = connection.execute(q).fetchone()[0]
    connection.close()
    return _count


def get_data_by_batch(count, predict_type, batch_size,
                      schema, table, date_info = False, **kwargs) -> pd.DataFrame:

    if not date_info:
        # if not chunk_by_source:
        for offset in range(0, count, batch_size):
            func = connect_database
            with func(schema=schema).cursor() as cursor:
                q = f"SELECT * FROM {table} " \
                    f"WHERE {predict_type} IS NOT NULL " \
                    f"LIMIT {batch_size} OFFSET {offset}"
                cursor.execute(q)
                result = to_dataframe(cursor.fetchall())
                yield result
                func(schema=schema).close()
        # else:
        #     assert condition != None, f'chunk_by_source is set to True while source_array is not found.'
        #     for offset in range(0, count, batch_size):
        #         func = connect_database
        #         with func(schema=schema).cursor() as cursor:
        #             q = f"SELECT * FROM {table} " \
        #                 f"WHERE s_id in {condition} " \
        #                 f"AND {predict_type} IS NOT NULL " \
        #                 f"LIMIT {batch_size} OFFSET {offset}"
        #             cursor.execute(q)
        #             result = to_dataframe(cursor.fetchall())
        #             yield result
        #             func(schema=schema).close()
    else:
        # if not chunk_by_source:
        for offset in range(0, count, batch_size):
            func = connect_database
            with func(schema=schema).cursor() as cursor:
                q = f"SELECT * FROM {table} " \
                    f"WHERE {predict_type} IS NOT NULL " \
                    f"AND post_time >= '{kwargs.get('start_time')}' " \
                    f"AND post_time <= '{kwargs.get('end_time')}' "\
                    f"LIMIT {batch_size} OFFSET {offset}"
                cursor.execute(q)
                result = to_dataframe(cursor.fetchall())
                yield result
                func(schema=schema).close()
        # else:
        #     assert condition != None, f'chunk_by_source is set to True while source_array is not found.'
        #     for offset in range(0, count, batch_size):
        #         func = connect_database
        #         with func(schema=schema).cursor() as cursor:
        #             q = f"SELECT * FROM {table} " \
        #                 f"WHERE s_id in {condition} " \
        #                 f"AND {predict_type} IS NOT NULL " \
        #                 f"AND post_time >= '{kwargs.get('start_time')}' " \
        #                 f"AND post_time <= '{kwargs.get('end_time')}' "\
        #                 f"LIMIT {batch_size} OFFSET {offset}"
        #             cursor.execute(q)
        #             result = to_dataframe(cursor.fetchall())
        #             yield result
        #             func(schema=schema).close()

def get_label_data_by_batch(task_id, count, batch_size, schema, table):
    for offset in range(0, count, batch_size):
        connection = connect_database(schema=schema, output=True)
        with connection.cursor() as cursor:
            q = f"SELECT * FROM {table} " \
                f"WHERE task_id = '{task_id}' " \
                f"LIMIT {batch_size} OFFSET {offset}"
            cursor.execute(q)
            result = to_dataframe(cursor.fetchall())
            yield result


def create_table(table_ID: str, logger: get_logger, schema=None):
    insert_sql = f'CREATE TABLE IF NOT EXISTS `{table_ID}`(' \
                 f'`id` VARCHAR(32) NOT NULL,' \
                 f'`task_id` VARCHAR(32) NOT NULL,' \
                 f'`source_author` TEXT(65535) NOT NULL,' \
                 f'`panel` VARCHAR(200) NOT NULL,' \
                 f'`create_time` DATETIME NOT NULL,' \
                 f'`field_content` TEXT(65535) NOT NULL,' \
                 f'`match_content` TEXT(1073741823) NOT NULL' \
                 f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                 f'AUTO_INCREMENT=1 ;'
    func = connect_database
    try:
        with func(schema, output=True).cursor() as cursor:
            logger.info('connecting to database...')
            logger.info('creating table...')
            cursor.execute(insert_sql)
            func(schema, output=True).close()
            logger.info(f'successfully created table {table_ID}')
    except Exception as e:
        logger.error(e)
        raise e


def create_state_table(logger: get_logger, schema=None):
    insert_sql = f'CREATE TABLE IF NOT EXISTS `state`(' \
                 f'`task_id` VARCHAR(32) NOT NULL,' \
                 f'`stat` VARCHAR(32) NOT NULL,' \
                 f'`prod_stat` VARCHAR (10),' \
                 f'`model_type` VARCHAR(32) NOT NULL,' \
                 f'`predict_type` VARCHAR(32) NOT NULL,' \
                 f'`date_range` TEXT(1073741823),' \
                 f'`target_table` VARCHAR(32) NOT NULL,' \
                 f'`create_time` DATETIME NOT NULL,' \
                 f'`peak_memory` FLOAT(10),' \
                 f'`length_receive_table` INT(11),' \
                 f'`length_output_table` INT(11),' \
                 f'`length_prod_table` INT(11),' \
                 f'`result` TEXT(1073741823),' \
                 f'`rate_of_label` INT(11),' \
                 f'`run_time` FLOAT(10),' \
                 f'`check_point` DATETIME' \
                 f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                 f'AUTO_INCREMENT=1 ;'
    func = connect_database
    try:
        with func(schema, output=True).cursor() as cursor:
            logger.info('connecting to database...')
            logger.info('creating table...')
            cursor.execute(insert_sql)
            func(schema, output=True).close()
            logger.info(f'successfully created table.')
    except Exception as e:
        logger.error(e)
        raise e



def insert2state(task_id, status, model_type, predict_type,
                 date_range, target_table, time, result,
                 logger: get_logger, schema=None):
    config = {
        'host': DatabaseInfo.output_host,
        'port': DatabaseInfo.output_port,
        'user': DatabaseInfo.output_user,
        'password': DatabaseInfo.output_password,
        'db': schema,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }

    connection = pymysql.connect(**config, write_timeout=30)

    insert_sql = f'INSERT INTO state ' \
                 f'(task_id, stat, model_type, predict_type, date_range, target_table, create_time, result) ' \
                 f'VALUES (' \
                 f'"{task_id}", ' \
                 f'"{status}", ' \
                 f'"{model_type}", ' \
                 f'"{predict_type}", ' \
                 f'"{date_range}", ' \
                 f'"{target_table}", ' \
                 f'"{time}", ' \
                 f'"{result}");'
    try:
        cursor = connection.cursor()
        logger.info('connecting to database...')
        cursor.execute(insert_sql)
        logger.info(f'successfully insert state into table.')
        connection.commit()
        connection.close()
    except Exception as e:
        raise e

def update2state(task_id, result, logger: get_logger, input_row_length = None,
                 output_row_length = None, run_time=None, schema=None, success=True,
                 check_point=None):
    config = {
        'host': DatabaseInfo.output_host,
        'port': DatabaseInfo.output_port,
        'user': DatabaseInfo.output_user,
        'password': DatabaseInfo.output_password,
        'db': schema,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }

    connection = pymysql.connect(**config, write_timeout=30)
    if success:
        insert_sql = f'UPDATE state ' \
                     f'SET stat = "SUCCESS", result = "{result}", ' \
                     f'length_receive_table = {input_row_length}, ' \
                     f'length_output_table = {output_row_length}, ' \
                     f'run_time = {run_time} ' \
                     f'Where task_id = "{task_id}"'
    else:
        insert_sql = f'UPDATE state ' \
                     f'SET stat = "FAILURE", result = "{result}", check_point = "{check_point}" ' \
                     f'Where task_id = "{task_id}"'


    try:
        cursor = connection.cursor()
        logger.info('connecting to database...')
        cursor.execute(insert_sql)
        logger.info(f'successfully write state into table.')
        connection.commit()
        connection.close()
    except Exception as e:
        raise e

def update_memory_time_to_state(task_id, time_data: float, memory_usage: int, logger: get_logger, schema=None):
    config = {
        'host': DatabaseInfo.output_host,
        'port': DatabaseInfo.output_port,
        'user': DatabaseInfo.output_user,
        'password': DatabaseInfo.output_password,
        'db': schema,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }

    connection = pymysql.connect(**config)

    insert_sql = f'UPDATE state ' \
                 f'SET run_time = {time_data}, ' \
                 f'peak_memory = {memory_usage} ' \
                 f'Where task_id = "{task_id}"'

    try:
        cursor = connection.cursor()
        logger.info('connecting to database...')
        cursor.execute(insert_sql)
        logger.info(f'successfully write resource statement into table.')
        connection.commit()
        connection.close()
    except Exception as e:
        raise e


def insert_table(table_ID: str, logger: get_logger, df):
    if SOURCE.get(table_ID):
        logger.info('connect to database...')
        engine = create_engine(DatabaseInfo.output_engine_info.value).connect()
        exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]
        engine.close()

        if SOURCE.get(table_ID) in exist_tables:
            pass
        else:
            logger.info(f'no table {SOURCE.get(table_ID)} in schema {DatabaseInfo.output_schema}, '
                        f'start creating one...')
            create_table(table_ID, logger)

        logger.info(f'write dataframe into table {SOURCE.get(table_ID)}')
        try:
            connection = engine.connect()
            df.to_sql(name=SOURCE.get(table_ID), con=connection, if_exists='append', index=False)
            logger.info(f'success, plz check {SOURCE.get(table_ID)}')
            connection.close()
        except:
            logger.error(f'write dataframe to {SOURCE.get(table_ID)} failed!')

    else:
        logger.error('table_name is not found')
        return

def drop_table(table_name: str, logger: get_logger, schema=None) :
    """drop table name"""
    drop_sql = f'DROP TABLE {table_name};'
    func = connect_database
    try:
        with func(schema=schema, output=True).cursor() as cursor:
            logger.info('connecting to database...')
            logger.info('dropping table...')
            cursor.execute(drop_sql)
            func(schema=schema, output=True).close()
            logger.info(f'successfully dropped table {table_name}')
    except Exception as e:
        logger.error('Cannot drop the table')
        raise e

def result_to_db(save_dir: SAVE_FOLDER, file_name: str, logger: get_logger):
    file_path = Path(save_dir / file_name)
    df = pd.read_csv(file_path, encoding='utf-8')

    for k in tqdm(SOURCE.keys()):
        start = datetime.now()
        temp = df[df['source_id'] == k]
        if len(temp) == 0:
            continue
        else:
            logger.info(f'start inserting data to table {SOURCE.get(k)}')
            insert_table(k, logger, temp)
            logger.info(f'complete inserting data to table {SOURCE.get(k)}')
            now = datetime.now()
            difference = now - start
            logger.info(f'writing table {SOURCE.get(k)} into db cost {difference.seconds} second')

    return f'Output file {file_name} is write into {DatabaseInfo.output_schema}'

def get_create_task_query(target_table, predict_type, start_time, end_time, get_all = False):

    if not get_all:
        q = f"SELECT * FROM {target_table} " \
            f"WHERE {predict_type} IS NOT NULL " \
            f"AND post_time >= '{start_time}'" \
            f"AND post_time <= '{end_time}'"
    else:
        q = f"SELECT * FROM {target_table} " \
            f"WHERE {predict_type} IS NOT NULL"

    return q

def get_count_query():
    return 'SELECT COUNT(task_id) FROM celery_taskmeta'

def get_tasks_query(table, order_column, number):
    q = f'SELECT * FROM {table} ' \
        f'ORDER BY {order_column} DESC ' \
        f'LIMIT {number} '

    return q

def get_sample_query(_id, tablename, number):
    q = f"(SELECT * FROM {tablename} WHERE task_id = '{_id}' " \
        f"AND rand() <= 0.2 " \
        f"LIMIT {number})"
    return q

def query_state(_id):
    q = f"SELECT * FROM state WHERE task_id = '{_id}'"
    return q

def get_result_query(_id, tablename):
    q = f"SELECT * FROM {tablename} WHERE task_id = '{_id} '"
    return q

def add_column(schema, table, col_name, col_type, **kwargs):

    if kwargs:
        condition = ''
        for k,v in kwargs.items():
            condition += f' {k} {v}'
    else:
        condition = ''
    connection = connect_database(schema=schema, output=True)
    q = f'ALTER TABLE {table} ' \
        f'ADD COLUMN {col_name} {col_type}'

    q += condition
    with connection.cursor() as cursor:
        cursor.execute(q)
        connection.close()

def get_distinct_count(schema, tablename, condition=None, start_time=None, end_time=None):
    info = f"mysql+pymysql://{os.getenv('INPUT_USER')}:{os.getenv('INPUT_PASSWORD')}@" \
           f"{os.getenv('INPUT_HOST')}:{os.getenv('INPUT_PORT')}/{schema}?charset=utf8mb4"
    connection = C(info).connect()
    # if date_info:
    if not connection:
        q = f'SELECT count(distinct s_id, author) ' \
            f'FROM {tablename} ' \
            f'WHERE author IS NOT NULL ' \
            f'AND s_id IS NOT NULL ' \
            f"AND post_time >= '{start_time}' " \
            f"AND post_time <= '{end_time}';"
    else:
        q = f'SELECT count(distinct s_id, author) ' \
            f'FROM {tablename} ' \
            f'WHERE author IS NOT NULL ' \
            f'AND s_id IS NOT NULL ' \
            f'AND s_id in {condition} ' \
            f"AND post_time >= '{start_time}' " \
            f"AND post_time <= '{end_time}';"
    # else:
    #     if not connection:
    #         q = f'SELECT count(distinct s_id, author) ' \
    #             f'FROM {tablename} ' \
    #             f'WHERE author IS NOT NULL and s_id IS NOT NULL;'
    #     else:
    #         q = f'SELECT count(distinct s_id, author) ' \
    #             f'FROM {tablename} ' \
    #             f'WHERE author IS NOT NULL and s_id IS NOT NULL ' \
    #             f'and s_id in {condition};'
    count = connection.execute(q).fetchone()[0]
    connection.close()

    return count

def get_label_source_from_state(task_id):
    connection = C(DatabaseInfo.output_engine_info).connect()
    q = f'SELECT target_table FROM state WHERE task_id = "{task_id}"; '
    source_name = connection.execute(q).fetchone()[0]
    connection.close()

    return source_name


def get_timedelta_query(predict_type, table, start_time, end_time):
    q = f"SELECT * FROM {table} " \
        f"WHERE {predict_type} IS NOT NULL " \
        f"AND post_time >= '{start_time}' " \
        f"AND post_time <= '{end_time}';"

    return q

def get_batch_by_timedelta(schema, predict_type, table,
                           begin_date: datetime, last_date: datetime,
                           interval: timedelta = timedelta(hours=6)):
    while begin_date <= last_date:

        connection = connect_database(schema=schema)

        if begin_date + interval > last_date:
            break

        else:
            start_date_interval = begin_date + interval
            cursor = connection.cursor()
            cursor.execute(get_timedelta_query(predict_type, table, begin_date, start_date_interval))
            result = to_dataframe(cursor.fetchall())
            begin_date += interval

            yield result, begin_date
            connection.close()







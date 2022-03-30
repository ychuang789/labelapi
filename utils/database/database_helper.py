import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

import pymysql
import pandas as pd
from retry import retry

from utils.enum_config import ModelType
from utils.general_helper import get_logger
from settings import DatabaseConfig
from workers.data_filter_builder import execute_data_filter


@retry(tries=5, delay=3)
def connect_database(schema=None, output=False, site_input: Optional[Dict] = None):
    if site_input:
        _config = site_input
        _config.update({
            'cursorclass': pymysql.cursors.DictCursor
        })
    else:
        if not output:
            _config = {
                'host': DatabaseConfig.INPUT_HOST,
                'port': DatabaseConfig.INPUT_PORT,
                'user': DatabaseConfig.INPUT_USER,
                'password': DatabaseConfig.INPUT_PASSWORD,
                'db': schema,
                'charset': 'utf8mb4',
                'cursorclass': pymysql.cursors.DictCursor
            }
        else:
            _config = {
                'host': DatabaseConfig.OUTPUT_HOST,
                'port': DatabaseConfig.OUTPUT_PORT,
                'user': DatabaseConfig.OUTPUT_USER,
                'password': DatabaseConfig.OUTPUT_PASSWORD,
                'db': schema,
                'charset': 'utf8mb4',
                'cursorclass': pymysql.cursors.DictCursor
            }
    try:
        connection = pymysql.connect(**_config)
        return connection

    except Exception as e:
        logging.error('Fail to connect to database.')
        raise e


def to_dataframe(data):
    return pd.DataFrame.from_dict(data)


def scrap_data_to_dict(query: str, schema: str):
    connection = connect_database(schema=schema, output=True)
    cur = connection.cursor()
    cur.execute(query)
    result = cur.fetchall()
    connection.close()
    return result


def create_table(table_ID: str, logger: get_logger, schema=None):
    insert_sql = f'CREATE TABLE IF NOT EXISTS `{table_ID}`(' \
                 f'`id` VARCHAR(32) NOT NULL,' \
                 f'`task_id` VARCHAR(32) NOT NULL,' \
                 f'`source_author` TEXT NOT NULL,' \
                 f'`panel` VARCHAR(200) NOT NULL,' \
                 f'`create_time` DATETIME NOT NULL,' \
                 f'`field_content` TEXT NOT NULL,' \
                 f'`match_content` LONGTEXT NOT NULL,' \
                 f'`match_meta` LONGTEXT NOT NULL' \
                 f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                 f'AUTO_INCREMENT=1 ;'
    connection = connect_database(schema=schema, output=True)
    try:
        cursor = connection.cursor()
        cursor.execute(insert_sql)
        cursor.close()
    except Exception as e:
        logger.error(e)
        raise e
    finally:
        connection.close()


# TODO: refactor
def drop_table(table_name: str, schema=None):
    drop_sql = f'DROP TABLE {table_name};'
    connection = connect_database(schema=schema, output=True)
    try:
        cursor = connection.cursor()
        cursor.execute(drop_sql)
        cursor.close()
        print('OK')
    except Exception as e:
        raise e
    finally:
        connection.close()


def get_sample_query(_id, tablename, number):
    q = f"(SELECT * FROM {tablename} WHERE task_id = '{_id}' " \
        f"AND rand() <= 0.2 " \
        f"LIMIT {number})"
    return q


def get_timedelta_query(predict_type, table, start_time, end_time):
    base = f"""SELECT * FROM {table} WHERE author IS NOT NULL AND s_id IS NOT NULL AND post_time >= '{start_time}' AND post_time <= '{end_time}'"""
    if isinstance(predict_type, str):
        q = base + f""" AND {predict_type} IS NOT NULL"""
        return q
    elif isinstance(predict_type, list):
        if len(predict_type) > 1:
            q = base
            for i in predict_type:
                q += f""" AND {i} IS NOT NULL"""
        else:
            q = base + f""" AND {predict_type[0]} IS NOT NULL"""

        return q
    else:
        raise TypeError(f'expect predict_type as type of list or str but get {type(predict_type)}')


def get_batch_by_timedelta(schema, predict_type, table,
                           begin_date: datetime, last_date: datetime,
                           interval: timedelta = timedelta(hours=6),
                           site_input: Optional[Dict] = None):
    try:
        connection = connect_database(schema=schema, site_input=site_input)
    except Exception as e:
        return str(e), begin_date

    while begin_date <= last_date:
        if begin_date + interval > last_date:
            connection.close()
            break
        else:
            start_date_interval = begin_date + interval
            try:
                cursor = connection.cursor()
                query = get_timedelta_query(predict_type, table, begin_date, start_date_interval)
                cursor.execute(query)
                # TODO: Add preprocessing module here to filter the input data set
                # result = to_dataframe(cursor.fetchall())
                data = cursor.fetchall()
                # result = to_dataframe(data)
                result = to_dataframe(execute_data_filter(dataset=data))
                yield result, begin_date
                begin_date += interval
                cursor.close()
            except Exception as e:
                yield e, begin_date
                connection.close()
                raise e





# some tools
def add_column(schema, table, col_name, col_type, **kwargs):
    if kwargs:
        condition = ''
        for k, v in kwargs.items():
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


def alter_column_type(schema: str, table_name: str, column_name: str, datatype: str) -> None:
    q = f"""ALTER TABLE {table_name} MODIFY {column_name} {datatype};"""
    connection = connect_database(schema, output=True)
    cur = connection.cursor()
    cur.execute(q)
    connection.close()


def get_batch_by_timedelta_new(schema, predict_type, table,
                               begin_date: datetime, last_date: datetime,
                               interval: timedelta = timedelta(hours=6), site_input=None):
    connection = connect_database(schema=schema, site_input=site_input)
    while begin_date <= last_date:
        if begin_date + interval > last_date:
            connection.close()
            break

        else:
            start_date_interval = begin_date + interval
            cursor = connection.cursor()
            cursor.execute(get_timedelta_query(predict_type, table, begin_date, start_date_interval))
            result = to_dataframe(cursor.fetchall())
            yield result, begin_date
            begin_date += interval
            cursor.close()

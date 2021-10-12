import os
import logging
from datetime import datetime
from pathlib import Path

import pymysql
import pandas as pd
from sqlmodel import SQLModel, create_engine
from tqdm import tqdm

from definition import SCRAP_FOLDER, SAVE_FOLDER
from utils.helper import get_logger
from utils.selections import QueryStatements
from settings import DatabaseInfo, SOURCE


def create_db(db_path, config_db):
    if os.path.exists(f'../{db_path}'):
        pass
    else:
        engine = create_engine(f'{config_db}', encoding='utf-8')
        SQLModel.metadata.create_all(engine)

def connect_database(schema = DatabaseInfo.input_schema):
        try:
            config = {
                'host': DatabaseInfo.host,
                'port': DatabaseInfo.port,
                'user': DatabaseInfo.user,
                'password': DatabaseInfo.password,
                'db': schema,
                'charset': 'utf8mb4',
                'cursorclass': pymysql.cursors.DictCursor,
            }
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

def scrap_data_to_df(logger: get_logger, query: str, schema: str = None, _to_dict: bool = False):
    func = connect_database
    # try:
    if schema:
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
    else:
        with func().cursor() as cursor:
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

    # except:
    #     logger.error(f'fail to scrap data')
    #     return 'fail to scrap data, probably caused by wrong query, plz re-check it'


def create_table(table_ID: str, logger: get_logger):
    if SOURCE.get(table_ID):
        insert_sql = f'CREATE TABLE IF NOT EXISTS `{SOURCE.get(table_ID)}`(' \
                     f'`source_id` VARCHAR(8) NOT NULL, ' \
                     f'`author` VARCHAR(200) NOT NULL,' \
                     f'`source_author` VARCHAR(200) NOT NULL,' \
                     f'`panel` VARCHAR(200) NOT NULL,' \
                     f'`applied_meta` TEXT(1073741823)' \
                     f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                     f'AUTO_INCREMENT=1 ;'
        func = connect_database
        try:
            with func(DatabaseInfo, write=True).cursor() as cursor:
                logger.info('connecting to database...')
                logger.info('creating table...')
                cursor.execute(insert_sql)
                func(DatabaseInfo, write=True).close()
                logger.info(f'successfully created table {SOURCE.get(table_ID)}')
        except:
            logger.error('Cannot create the table')
            return

    else:
        logger.error('table_name is not found')
        return


def insert_table(table_ID: str, logger: get_logger, df):
    if SOURCE.get(table_ID):
        logger.info('connect to database...')
        engine = create_engine(DatabaseInfo.engine_info.value)
        exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]

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
        except:
            logger.error(f'write dataframe to {SOURCE.get(table_ID)} failed!')

    else:
        logger.error('table_name is not found')
        return

def clean_up_table(table_name: str, logger: get_logger):
    """drop table name"""
    drop_sql = f'DROP TABLE {table_name};'
    func = connect_database
    try:
        with func(DatabaseInfo, write=True).cursor() as cursor:
            logger.info('connecting to database...')
            logger.info('dropping table...')
            cursor.execute(drop_sql)
            func(DatabaseInfo, write=True).close()
            logger.info(f'successfully dropped table {table_name}')
    except:
        logger.error('Cannot drop the table')
        return

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

def get_create_task_query(target_table, predict_type, start_time, end_time):

    q = f"SELECT * FROM {target_table} " \
        f"WHERE {predict_type} IS NOT NULL " \
        f"AND post_time >= '{start_time}'" \
        f"AND post_time <= '{end_time}'"

    return q

def get_count_query():
    return 'SELECT COUNT(task_id) FROM celery_taskmeta'

def get_tasks_query(table, order_column, offset, number):
    q = f'SELECT task_id, status FROM {table} ' \
        f'WHERE id >= (SELECT id FROM {table} ' \
        f'ORDER BY {order_column} ' \
        f'LIMIT {offset}, 1) ' \
        f'LIMIT {number}'

    return q

def get_sample_query(_id, string, order_column, offset, number):
    q = f"SELECT * FROM {string}WHERE task_id = '{_id.split(';')[0]}' " \
        f"AND id >= (SELECT id FROM {string}ORDER BY {order_column} " \
        f"LIMIT {offset},1) " \
        f"LIMIT {number}"

    return q

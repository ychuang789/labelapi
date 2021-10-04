import logging
from datetime import datetime

import pymysql
import pandas as pd

from definition import SCRAP_FOLDER
from settings import QueryStatements, DatabaseInfo


def connect_database(schema = DatabaseInfo.rule_schemas):
        try:
            config = {
                'host': DatabaseInfo.host.value,
                'port': DatabaseInfo.port.value,
                'user': DatabaseInfo.user.value,
                'password': DatabaseInfo.password.value,
                'db': schema.value,
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
            logger.error(f'fail to scrap data from {DatabaseInfo.schema.name}')
            return

    return file_list

def scrap_data_to_df(logger):
    func = connect_database
    for query in QueryStatements:
        try:
            with func().cursor() as cursor:
                logger.info('connecting to database...')
                cursor.execute(query.value)
                result = to_dataframe(cursor.fetchall())
                func().close()
                return result

        except:
            logger.error(f'fail to scrap data from {DatabaseInfo.schema.name}')
            return

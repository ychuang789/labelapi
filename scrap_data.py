import os
import argparse
from datetime import datetime

from definition import SCRAP_FOLDER, GET_DATA_QUERY
from utils.database_utils import connect_database, to_dataframe
from utils.helper import get_logger

_logger = get_logger('scrap_data')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=os.getenv('HOST'), help='host address')
    parser.add_argument('--user', default=os.getenv('DB_USER_ID'), help='user id')
    parser.add_argument('--password', default=os.getenv('DB_USER_PWD'), help='user password')
    args = parser.parse_args()

    date_time = datetime.now().strftime("%Y%m%d%H%M%S")
    func = connect_database
    with func('forum_data', args).cursor() as cursor:
        _logger.info('connecting to database...')
        sql = GET_DATA_QUERY
        cursor.execute(sql)
        result = to_dataframe(cursor.fetchall()).drop_duplicates()
        print(len(result))
        result.to_csv(f"{SCRAP_FOLDER}/data_{len(result)}_{date_time}.csv", encoding='utf-8-sig', index=None)
        _logger.info('saving results...')
        func('forum_data', args).close()

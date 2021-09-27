
import logging
import pymysql.cursors
import pandas as pd

def connect_database(db, args):
    try:
        config = {
            'host': args.host,
            'user': args.user,
            'password': args.password,
            'db':db,
            'charset':'utf8mb4',
            'cursorclass':pymysql.cursors.DictCursor,
        }
        connection = pymysql.connect(**config)
        return connection

    except:
        logging.error('Fail to connect to database.')


# def execute_srcaping(args):
#     start_time = time()
#     func = connect_database
#     sql_cmd = args.sql
#     with func('forum_data', args).cursor() as cursor:
#         # now = datetime.now().strftime("%m%d%Y%H%M%S")
#         cursor.execute(sql_cmd)
#         result = to_dataframe(cursor.fetchall()).drop_duplicates()
#         # result.to_pickle('./scrap_file/{0}_{1}.pkl'.format(now, len(result)))
#         print("The execution time is {} sec".format(time()-start_time))
#         func('forum_data', args).close()
#
#     return result

def to_dataframe(data):
    return pd.DataFrame.from_dict(data)

import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import pymysql
from sqlalchemy import create_engine

from definition import AUDIENCE_PRODUCTION_PATH
from settings import DatabaseConfig, TABLE_GROUPS_FOR_INDEX
from utils.database_core import connect_database, to_dataframe, create_table, drop_table
from utils.helper import get_logger

class TableMissingError(Exception):
    """missing table value"""
    pass

class QueryNotFoundError(Exception):
    """missing query"""
    pass

class ProductionTableNameNotFoundError(Exception):
    """cannot relate to the production table name, check settings.TABLE_GROUPS_FOR_INDEX"""
    pass

class OutputZIPNotFoundError(Exception):
    """output ZIP file not found"""
    pass

def get_query(**kwargs):
    table_name = kwargs.get('table_name')
    task_id = kwargs.get('task_id')
    query_dict = {
        "dump_info": f"""select task_id, result from {table_name} where task_id = '{task_id}'""",
        "check_table_exist": f"""select * from information_schema.tables where table_name = '{table_name}'""",
        "get_production_data": f"""select * from {table_name} where task_id = '{task_id}'""",
        "check_duplicate_data": f"""SELECT source_author, panel, COUNT(*) as c 
        FROM {table_name} GROUP BY source_author, panel HAVING c > 1;""",
        "change_table_name": f"""ALTER TABLE {table_name} RENAME {table_name}_old;""",
        "get_source_schema_name": f"""select target_table from state where task_id = '{task_id}';""",
    }

    return query_dict

def alter_table(connection: pymysql.connect, query: str, condition: List[str] = None) -> None:
    if condition:
        _condition = ''
        for i in condition:
            _condition += f' {i}'
        query += f' {_condition}'
    else:
        pass

    cur = connection.cursor()
    cur.execute(query)
    connection.commit()
    connection.close()

def get_data(connection: pymysql.connect, query: str, condition: List[str] = None, _fetchone: bool=False):
    if condition:
        _condition = ''
        for i in condition:
            _condition += f' {i}'
        query += f' {_condition}'
    else:
        pass

    cur = connection.cursor()
    cur.execute(query)
    if _fetchone:
        result = cur.fetchone()
    else:
        result = cur.fetchall()

    connection.close()
    return result

def get_dump_info(**kwargs) -> Dict[str, str]:
    schema = kwargs.get('schema')
    connection = connect_database(schema=schema, output=True)
    return get_data(connection, get_query(**kwargs).get('dump_info'), _fetchone=True)

def check_table_exist(_table_name: str, **kwargs) -> Optional[Dict[str, str]]:
    query_dict = get_query(**kwargs)
    if not query_dict.get('check_table_exist'):
        raise QueryNotFoundError('Query not found, cannot check if dump tables are exist')

    schema = kwargs.get('schema')
    kwargs.update({'table_name': _table_name})
    connection = connect_database(schema=schema, output=True)

    return get_data(connection, get_query(**kwargs).get('check_table_exist'), _fetchone=True)


def get_dump_table_name(**kwargs) -> List:
    # after `get_dump_info`
    if kwargs.get('result'):
        if ',' in kwargs.get('result'):
            if 'wh_panel_mapping_' not in kwargs.get('result'):
                temp_table_name = kwargs.get('result').split(',')
                table_name = ['wh_panel_mapping_'+ i for i in temp_table_name]
            else:
                table_name = kwargs.get('result').split(',')
        else:
            if 'wh_panel_mapping_' not in kwargs.get('result'):
                table_name = [f'wh_panel_mapping_{kwargs.get("result")}']
            else:
                table_name = [kwargs.get('result')]

        return table_name
    else:
        raise TableMissingError("missing table_name information in arguments")

def generate_zip(table_name: List, source_db_name: str, production_path = AUDIENCE_PRODUCTION_PATH):
    host = DatabaseConfig.OUTPUT_HOST
    port = DatabaseConfig.OUTPUT_PORT
    user = DatabaseConfig.OUTPUT_USER
    password = DatabaseConfig.OUTPUT_PASSWORD
    schema = DatabaseConfig.OUTPUT_SCHEMA
    today = datetime.now().strftime("%Y%m%d%H%M%S")
    path = f'{production_path}/{source_db_name}_{today}'

    check_path = path + '/'
    if not os.path.isdir(check_path):
        os.mkdir(check_path)

    for tb in table_name:

        command = f"""
        mysqldump -u{user} -p{password} -h{host} -P{port} --lock-tables=false {schema} {tb} | zip > {path}/{tb}.zip
        """
        os.system(command)


    for tb in table_name:
        if not os.path.isfile(check_path + f'{tb}.zip'):
            raise OutputZIPNotFoundError(f'table {tb} writing to ZIP failed...')



def get_production_dict(table_list):
    _d = defaultdict(list)
    for i in table_list:
        _temp_table_name = i.split('_')[-1]
        for k,v in TABLE_GROUPS_FOR_INDEX.items():
            if _temp_table_name in v:
                if _d.get(k):
                    _d[k].append(i)
                else:
                    _d.update({k: [i]})

    if len(_d) == 0:
        raise ProductionTableNameNotFoundError('cannot relate to the '
                                               'production table name, check '
                                               'settings.TABLE_GROUPS_FOR_INDEX')
    return dict(_d)

def get_source_db_name(**kwargs):
    schema = kwargs.get('schema')
    connection = connect_database(schema=schema, output=True)
    return get_data(connection, get_query(**kwargs).get('get_source_schema_name'), _fetchone=True)


def get_last_production(logger: get_logger, **kwargs):
    schema = kwargs.get('schema')
    source_db_name = get_source_db_name(**kwargs).get('target_table')
    logger.info('getting dump table info ...')
    table_name = get_dump_table_name(**get_dump_info(**kwargs))
    production_dict = get_production_dict(table_name)


    kwargs.pop('table_name')

    logger.info('start generate last production table ...')
    for key, table_name in production_dict.items():

        df_production = pd.DataFrame(columns=['id',
                                              'task_id',
                                              'source_author',
                                              'panel',
                                              'create_time',
                                              'field_content',
                                              'match_content'])

        for _table_name in table_name:
            if not check_table_exist(_table_name, **kwargs):
                logger.error(f'table {_table_name} not found!')
                raise TableMissingError(f'table {_table_name} not found!')

            kwargs.update({'table_name': _table_name})
            connection = connect_database(schema=schema, output=True)
            is_duplicated = get_data(connection,
                                     get_query(**kwargs).get('check_duplicate_data'))

            connection = connect_database(schema=schema, output=True)
            result = get_data(connection,
                              get_query(**kwargs).get('get_production_data'))

            df = to_dataframe(result)

            if is_duplicated:

                df['source_author'] = df['source_author'].str.strip()
                df = df.drop_duplicates(subset=['source_author', 'panel'], keep='last')

                connection = connect_database(schema=schema, output=True)
                alter_table(connection, get_query(**kwargs).get('change_table_name'))
                create_table(_table_name, get_logger('scrap_data'), schema=schema)

                _con = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO).connect()
                df.to_sql(name=_table_name, con=_con, if_exists='append', index=False)
                _con.close()
                df_production = df_production.append(df)

        production_table_name = f"wh_panel_mapping_{key}"
        if check_table_exist(production_table_name, **kwargs):
            temp_production_table_name = f'{production_table_name}_old'
            if check_table_exist(temp_production_table_name, **kwargs):
                drop_table(temp_production_table_name, logger, schema=schema)
                kwargs.update({'table_name': production_table_name})
                connection = connect_database(schema=schema, output=True)
                alter_table(connection,
                            get_query(**kwargs).get('change_table_name'))

        create_table(production_table_name, get_logger('scrap_data'), schema=schema)

        _con = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO).connect()

        logger.info(f'start writing data into {production_table_name} ...')
        try:
            df_production.to_sql(name=production_table_name, con=_con, if_exists='append', index=False)
        except Exception as ex:
            logger.error(ex)
            raise ex

        temp_table_to_delete = f'{production_table_name}_old'
        if check_table_exist(temp_table_to_delete, **kwargs):
            logger.info(f'start dropping old table {temp_table_to_delete} ...')
            drop_table(temp_table_to_delete, get_logger("scrap_data"), schema=schema)

    logger.info('start generating audience production ZIP ...')
    last_table = ['wh_panel_mapping_' + i for i in list(production_dict.keys())]
    generate_zip(last_table,source_db_name)


















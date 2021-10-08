import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

from sqlalchemy import create_engine
from tqdm import tqdm
import pandas as pd

from definition import SAVE_FOLDER
from models.rule_model import RuleModel
from models.keyword_model import  KeywordModel
from settings import DatabaseInfo
from utils.database_core import scrap_data_to_df, connect_database
from utils.helper import get_logger
from utils.selections import ModelType, PredictTarget
from utils.input_example import InputExample


def run_prediction(input_examples: Iterable[InputExample], pattern: Dict,
                   model_type: str,
                   predict_type: PredictTarget):
    if model_type == "rule_model":
        label_model = RuleModel(pattern)
        matched_labels, match_count_list = label_model.predict(input_examples, target=predict_type)
        return matched_labels, match_count_list
    elif model_type == "keyword_model":
        label_model = KeywordModel(pattern)
        matched_labels, match_count_list = label_model.predict(input_examples, target=predict_type)
        return matched_labels, match_count_list


def convert_input_data(df: pd.DataFrame) -> Iterable[InputExample]:
    input_examples = []
    for _, row in df.iterrows():
        input_example = InputExample(
            id_= row.id,
            s_area_id = row.source_author[:8],
            author = row.source_author[9:],
            title = "",
            content = row.applied_content ,
            post_time = row.created_at
        )
        input_examples.append(input_example)
        
    return input_examples

def labeling(_id:str, df: pd.DataFrame, model_type: str,
             predict_type: str, pattern: Dict, logger: get_logger, to_database=False):
    start = datetime.now()
    logger.info(f'start labeling at {start} ...')
    if model_type == ModelType.RULE_MODEL.value:
        model = RuleModel(pattern)
        temp_list = []
        for i in tqdm(range(len(df))):
            _input_data = InputExample(
                id_=df['id'].iloc[i],
                s_area_id=df['source_author'].iloc[i][:8],
                author=df['source_author'].iloc[i][9:],
                title="",
                content=df['applied_content'].iloc[i],
                post_time=df['created_at'].iloc[i]
            )
            rs, prob = model.predict([_input_data], target=predict_type)

            if rs:
                if len(rs) == 1:
                    temp_list.append(rs[0][0])
            else:
                temp_list.append('')

        df['panel'] = temp_list
        df['task_id'] = [_id for i in range(len(df))]

    elif model_type == ModelType.KEYWORD_MODEL.value:
        model = KeywordModel(pattern)
        temp_list = []
        for i in tqdm(range(len(df))):
            _input_data = InputExample(
                id_=df['id'].iloc[i],
                s_area_id=df['source_author'].iloc[i][:8],
                author=df['source_author'].iloc[i][9:],
                title="",
                content=df['applied_content'].iloc[i],
                post_time=df['created_at'].iloc[i]
            )
            rs, prob = model.predict([_input_data], target=predict_type)

            if rs:
                if len(rs) == 1:
                    temp_list.append(rs[0][0])
            else:
                temp_list.append('')

        df['panel'] = temp_list
        df['task_id'] = [_id for i in range(len(df))]

    else:
        logger.error('wrong model name input')
        return


    # df = df[['id', 'task_id', 'source_author', 'created_at', 'panel']]

    logger.info('finish labeling, generate the output ...')
    df["panel"].replace({"female": "/female", "male": "/male"}, inplace=True)
    df.rename(columns={'created_at': 'create_time'}, inplace=True)
    df.rename(columns={'source_author': 'source_id'}, inplace=True)

    df['field_content'] = [i[:8] for i in df['source_id'].values.tolist()]
    df['matched_content'] = [i[9:] for i in df['source_id'].values.tolist()]

    df_output = df[['id', 'task_id', 'source_id', 'create_time', 'panel', 'field_content', 'matched_content']]

    if to_database:
        logger.info(f'write the output into database ...')
        start = datetime.now()
        create_table_query = f'CREATE TABLE IF NOT EXISTS `test`(' \
                             f'`id` INT(11) NOT NULL, ' \
                             f'`task_id` VARCHAR(32) NOT NULL,' \
                             f'`source_id` VARCHAR(200) NOT NULL,' \
                             f'`panel` VARCHAR(200) NOT NULL,' \
                             f'`create_time` DATETIME NOT NULL,' \
                             f'`field_content` VARCHAR(8) NOT NULL,' \
                             f'`matched_content` VARCHAR(200) NOT NULL' \
                             f')ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ' \
                             f'AUTO_INCREMENT=1 ;'


        engine = create_engine(DatabaseInfo.engine_info)

        exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]

        if 'test' in exist_tables:
            pass
        else:
            logger.info(f'no table test in schema {DatabaseInfo.output_schema}, '
                        f'start creating one...')
            # try:
            with connect_database(DatabaseInfo.output_schema).cursor() as cursor:
                logger.info('connecting to database...')
                logger.info('creating table...')
                cursor.execute(create_table_query)
                connect_database(DatabaseInfo.output_schema).close()
                logger.info(f'successfully created table test')
            # except:
            #     logger.error('Cannot create the table')
            #     return


        logger.info(f'write dataframe into table test')
        try:
            connection = engine.connect()
            df_output.to_sql(name='test', con=connection, if_exists='append', index=False)
            now = datetime.now()
            difference = now - start
            logger.info(f'writing table test into db cost {difference.total_seconds()} second')
            return f'writing table test into db cost {difference.total_seconds()} second'
        except:
            logger.error(f'write dataframe to test failed!')
            return


    else:
        logger.info('write the output into local folder ...')
        now = datetime.now()
        time_diff = now - start

        file_path = Path(SAVE_FOLDER / f'output_{len(df_output)}_{round(time_diff.total_seconds())}.csv')
        logger.info(f'saving file to {SAVE_FOLDER}')
        df_output.to_csv(file_path, index=False, encoding='utf-8-sig')
        logger.info(f'file is saved as output_{len(df_output)}_{round(time_diff.total_seconds())}.csv')

        _output = json.dumps(f'output_{len(df_output)}_{round(time_diff.total_seconds())}.csv')

        return _output




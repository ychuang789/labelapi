import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional, Union, Tuple, List

from sqlalchemy import create_engine
from tqdm import tqdm
import pandas as pd

from definition import SAVE_FOLDER
from models.rule_model import RuleModel
from models.keyword_model import  KeywordModel

from definition import RULE_FOLDER
from settings import DatabaseInfo, SOURCE
from utils.database_core import connect_database, create_table
from utils.helper import get_logger
from utils.selections import ModelType, PredictTarget, KeywordMatchType
from utils.input_example import InputExample


def read_key_word_pattern(file_path: Optional[Union[str, Path]], _key: str) -> Dict[str, List[Tuple[str, KeywordMatchType]]]:
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()
        values = [(line.split("\t")[0],line.split("\t")[1]) for line in lines]
        output_dict = {_key: values}
        return output_dict

def read_from_dir(model_type: Union[ModelType, str],
                  predict_type: Union[PredictTarget, str])-> Dict[str, List[Tuple[str, KeywordMatchType]]]:
    _dict = {}
    for gender in os.listdir(f'{RULE_FOLDER}/{model_type}'):
        for file in os.listdir(f'{RULE_FOLDER}/{model_type}/{gender}'):
            if file.endswith(".txt"):
                file_path = Path(RULE_FOLDER / model_type / gender / f'{predict_type}.txt')
                _dict.update(read_key_word_pattern(file_path, gender))

    return _dict


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
        for i in range(len(df)):
            _input_data = InputExample(
                id_=df['id'].iloc[i],
                s_area_id=df['s_area_id'].iloc[i],
                author=df['author'].iloc[i],
                title=df['title'].iloc[i],
                content=df['content'].iloc[i],
                post_time=df['post_time'].iloc[i]
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
        for i in range(len(df)):
            _input_data = InputExample(
                id_=df['id'].iloc[i],
                s_area_id=df['s_area_id'].iloc[i],
                author=df['author'].iloc[i],
                title=df['title'].iloc[i],
                content=df['content'].iloc[i],
                post_time=df['post_time'].iloc[i]
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
        raise ValueError('wrong model name input, please check the input')


    # df = df[['id', 'task_id', 'source_author', 'created_at', 'panel']]

    # logger.info('finish labeling, generate the output ...')
    df["panel"].replace({"female": "/female", "male": "/male"}, inplace=True)
    df.rename(columns={'post_time': 'create_time'}, inplace=True)
    df['source_author'] = df['s_id'] + '_' + df['author']
    df['field_content'] = df['s_id']
    if predict_type == PredictTarget.AUTHOR_NAME.value:
        df['match_content'] = df['author']
    else:
        df['match_content'] = df[predict_type]

    df_output = df[['id', 'task_id', 'source_author', 'create_time',
                    'panel', 'field_content', 'match_content']]

    df_output.dropna(subset=['panel'], inplace=True)

    if to_database:
        logger.info(f'write the output into database ...')

        engine = create_engine(DatabaseInfo.output_engine_info, pool_size=0, max_overflow=-1)
        exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]
        result_table_list = []

        for k,v in SOURCE.items():
            df_write = df_output[df_output['field_content'].isin(v)]

            if df_write.empty:
                continue

            _table_name = f'wh_panel_mapping_{k}'
            if _table_name not in exist_tables:
                create_table(k,logger, schema=DatabaseInfo.output_schema)

            try:
                connection = engine.connect()
                df_write.to_sql(name=_table_name, con=connection, if_exists='append', index=False)
                logger.info(f'successfully write data into {DatabaseInfo.output_schema}.{_table_name}')
            except:
                logger.error(f'write dataframe to test failed!')
                raise ConnectionError(f'failed to write output into {DatabaseInfo.output_schema}.{_table_name}... '
                                      f'probable wrong query or connection issue')
            result_table_list.append(_table_name)
        return result_table_list

    else:
        logger.info('write the output into local folder ...')
        now = datetime.now()
        time_diff = now - start

        file_path = Path(SAVE_FOLDER / f'output_{len(df_output)}_{round(time_diff.total_seconds())}.csv')
        logger.info(f'saving file to {SAVE_FOLDER}')
        df_output.to_csv(file_path, index=False, encoding='utf-8-sig')
        logger.info(f'file is saved as output_{len(df_output)}_{round(time_diff.total_seconds())}.csv')

        _output = f'output_{len(df_output)}_{round(time_diff.total_seconds())}.csv'

        return _output


def generate_test():
    temp = 0
    b = 1
    for i in range(100000):
        a = temp
        b += a
        temp = b

    return temp

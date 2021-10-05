import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable
from tqdm import tqdm
import pandas as pd

from definition import SAVE_FOLDER
from models.audience_models import RuleModel, KeywordModel
from utils.database_core import scrap_data_to_df
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

def labeling(model_type: str, predict_type: str, pattern_path: Path, logger: get_logger):
    start = datetime.now()
    pattern = pd.read_pickle(pattern_path)
    df = scrap_data_to_df(logger)
    if model_type == ModelType.RULE_MODEL.value:
        model = RuleModel(pattern)
        temp_list = []
        for i in range(len(df)):
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

    elif model_type == ModelType.KEYWORD_MODEL.value:
        model = KeywordModel(pattern)
        temp_list = []
        for i in range(len(df)):
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
    else:
        logger.error('wrong model name input')

    now = datetime.now()
    time_diff = now - start

    file_path = Path(SAVE_FOLDER / f'output_{len(df)}_{round(time_diff.total_seconds())}.csv')
    logger.info(f'saving file to {SAVE_FOLDER}')
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    logger.info(f'file is saved as output_{len(df)}_{round(time_diff.total_seconds())}.csv')

    return f'output_{len(df)}_{round(time_diff.total_seconds())}.csv'




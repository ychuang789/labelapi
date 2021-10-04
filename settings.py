import os
from enum import  Enum

from dotenv import load_dotenv

INPUT_COLUMNS = "source_author, applied_content, created_at"

SYSTEM_CONFIG = {'settings':
                     {'database':
                          {'author_cache': 1000, 'document_batch': 1000, 'fetch_limit': -1, 'connect_timeout': 30, 'connect_retries': 1},
                      'logger':
                          {'logging_fmt': '[%(asctime)s][{_context}][%(levelname)s]: %(message)s',
                           'logging_fmt_err': '[%(asctime)s][{_context}][%(funcName)s()][%(levelname)s]: %(message)s',
                           'log_backup_count': 30},
                      'content':
                          {'stopwords':
                               {'files': ['files/stopWords.txt']},
                           'blacklist_patterns':
                               {'files': [None]}, 'min_doc_length': 1, 'max_doc_length': 2000},
                      'compare_file':
                          {'files':
                               {'forum': 'files/forum_convert.xlsx',
                                'social': 'files/social_convert.xlsx',
                                'comment': 'files/comment_convert.xlsx',
                                'qa': 'files/qa_convert.xlsx',
                                'blog': 'files/blog_convert.xlsx',
                                'news': 'files/news_convert.xlsx'}
                           }
                      }
                 }


class ModelType(Enum):
    RULE_MODEL = "rule_model"
    KEYWORD_MODEL = "keyword_model"

class PredictTarget(Enum):
    CONTENT = "content"
    AUTHOR_NAME = "author_name"
    S_AREA_ID = "s_area_id"

class KeywordMatchType(Enum):
    PARTIALLY = "partially"
    ABSOLUTELY = "absolutely"
    START = "start"
    END = "end"

class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predict target type."

class CeleryConfig:
    name = 'celery_worker'
    backend='redis://localhost/0'
    broker = 'redis://localhost'
    timezone = 'Asia/Taipei'
    enable_utc = False
    result_expires = None

class DatabaseInfo(Enum):
    load_dotenv()
    host = os.getenv('HOST')
    port = int(os.getenv('PORT'))
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    input_schema = os.getenv('INPUT_SCHEMA')
    output_schema = os.getenv('OUTPUT_SCHEMA')
    rule_schemas = os.getenv('RULE_SHEMAS')
    engine_info = f'mysql+pymysql://{user}:{password}@{host}:{port}/{output_schema}?charset=utf8mb4'

class QueryStatements(Enum):
    # QUERY_FEMALE = f'SELECT {INPUT_COLUMNS} FROM predicting_jobs_predictingresult WHERE label_name LIKE "女%" AND applied_feature="author"'
    # QUERY_MALE = f'SELECT {INPUT_COLUMNS} FROM predicting_jobs_predictingresult WHERE label_name LIKE "男%" AND applied_feature="author"'
    MALE_RULE = f'SELECT * FROM male_author_name_rules'
    FEMALE_RULE = f'SELECT * FROM female_author_name_rules'

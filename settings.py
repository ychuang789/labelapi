import os
from dotenv import load_dotenv

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


class CeleryConfig:
    name = 'celery_worker'
    backend='redis://localhost/0'
    broker = 'redis://localhost'
    timezone = 'Asia/Taipei'
    enable_utc = False
    result_expires = None

class DatabaseInfo:
    load_dotenv()
    host = os.getenv('HOST')
    port = int(os.getenv('PORT'))
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    input_schema = os.getenv('INPUT_SCHEMA')
    output_schema = os.getenv('OUTPUT_SCHEMA')
    rule_schemas = os.getenv('RULE_SHEMAS')
    engine_info = f'mysql+pymysql://{user}:{password}@{host}:{port}/{output_schema}?charset=utf8mb4'



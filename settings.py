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

DATA_CONFIG = {'source_name_1':
                   {'input':
                         {'host': '172.18.20.190',
                          'port': 3306,
                          'user': 'rd2',
                          'pwd': 'eland4321',
                          'schema': 'audience-toolkit-django',
                          'table': 'predicting_jobs_predictingresult'
                          }
                         },
                    'output':
                        {'host': '172.18.20.190',
                         'port': 3306,
                         'user': 'rd2',
                         'pwd': 'eland4321',
                         'schema': 'audience_result'
                         }
                }

MODEL_CONFIG = {'gender_model_1':
                    {'model_type': 'keyword_model',
                     'model_settings':
                         {'case_sensitive': False,
                          'target': 'author_name'
                          },
                     'model_data':
                         {'files': ['rules/author_name.pkl']
                          }
                     }
                }


SOURCE = {'WH_F0183': 'Comment',
          'WH_F0116': 'Dcard',
          'WH_F0001': 'Ptt',
          'WH_F0147': 'Youtube',
          'WH_F0157': 'Instagram',
          'WH_F0501': 'Tiktok',
          'WH_F0127': 'Twitter',
          'WH_F0045': 'fbfans',
          'WH_F0165': 'fbgroup',
          'WH_F0071': 'fbkol',
          'WH_F0167': 'fbprivategroup',
          'WH_F0038': 'plurk',
          'WH_F0002': 'forum',
          'WH_B0002': 'blog',
          'WH_CTN0026': 'news'}


class CeleryConfig:
    name = 'celery_worker'
    sql_uri = 'sqlite:///save.db'
    backend = 'db+sqlite:///save.db'
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



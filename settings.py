from enum import  Enum

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

class Errors(Enum):
    UNKNOWN_DB_TYPE = "Unknown database type."
    UNKNOWN_PREDICT_TARGET_TYPE = "Unknown predict target type."





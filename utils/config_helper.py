import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from definition import DEFAULT_CONFIG

@dataclass()
class _ContentSettings:
    # content_length
    min_doc_length: int = field(default=1)  # chars
    max_doc_length: int = field(default=2000)  # chars

    stopwords: Dict[str, Union[Dict, List]] = field(default=None)
    blacklist_patterns: Dict[str, Union[Dict, List, None]] = field(default=None)

@dataclass()
class _CompareFileFormat:
    files: Dict[str, Optional[Dict]] = field(default=None)

@dataclass()
class _LoggerSettings:
    logging_fmt: str = field(default="[%(asctime)s][{_context}][%(levelname)s]: %(message)s")
    logging_fmt_err: str = field(default="[%(asctime)s][{_context}][%(funcName)s()][%(levelname)s]: %(message)s")
    log_backup_count: int = field(default=30)  # days
    log_verbose: bool = field(default=False)

@dataclass()
class _DatabaseSettings:
    author_cache: int = field(default=30)
    document_batch: int = field(default=2000)
    fetch_limit: int = field(default=-1)
    connect_timeout: int = field(default=30)  # sec
    connect_retries: int = field(default=1)

class StaticConfigs:
    _static_settings_field_name = "settings"
    _logger_settings_field_name = "logger"
    _database_settings_field_name = "database"
    _content_settings_field_name = "content"
    _compare_file_settings_field_name = "compare_file"
    _static_settings = {}

    try:
        with open(DEFAULT_CONFIG, "r") as stream:
            _configs = yaml.load(stream, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print(f"找不到設定檔:'{DEFAULT_CONFIG}'，將使用預設值。或檢查'definition.py'中'DEFAULT_CONFIG'路徑設定是否正確")
        _configs = {}
    # init static settings
    try:
        _static_settings = _configs[_static_settings_field_name]
    except KeyError:
        print(f"找不到欄位:'{_static_settings_field_name}'，將使用預設值。")

    # init logger settings
    try:
        _log_setting_data = _static_settings[_logger_settings_field_name]
        logger_settings = _LoggerSettings(**_log_setting_data)
    except KeyError:
        print(f"找不到欄位:'{_logger_settings_field_name}'，將使用預設值。")
        logger_settings = _LoggerSettings()

    # init database settings
    try:
        _database_setting_data = _static_settings[_database_settings_field_name]
        database_setting = _DatabaseSettings(**_database_setting_data)
    except KeyError:
        print(f"找不到欄位:'{_database_settings_field_name}'，將使用預設值。")
        database_setting = _DatabaseSettings()

    # init content settings
    try:
        _content_setting_data = _static_settings[_content_settings_field_name]
        content_setting = _ContentSettings(**_content_setting_data)
    except KeyError:
        print(f"找不到欄位:'{_content_settings_field_name}'，將使用預設值。")
        content_setting = _ContentSettings()

    # init compare file settings
    try:
        _compare_file_format_setting_data = _static_settings[_compare_file_settings_field_name]
        compare_file_format_setting = _CompareFileFormat(**_compare_file_format_setting_data)
    except KeyError:
        print(f"找不到欄位:'{_compare_file_settings_field_name}'，將使用預設值。")
        compare_file_format_setting = _CompareFileFormat()

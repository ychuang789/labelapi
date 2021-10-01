import os
import logging
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

from definition import ROOT_LOG_DIR

def get_error_file_handler(logger_name) -> Any:
    log_dir = os.path.join(ROOT_LOG_DIR, logger_name)
    Path(log_dir).mkdir(exist_ok=True)
    filepath = os.path.join(
        log_dir,
        time.strftime("%Y-%m-%d", time.localtime()) + ".error.log"
    )
    file_handler = TimedRotatingFileHandler(
        filepath, when='midnight', backupCount=30, encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s][<PID %(process)d:%(processName)s>]"
        "[%(name)s.%(funcName)s()][%(levelname)s] "
        "%(message)s"
    ))
    return file_handler

def get_normal_file_handler(logger_name, log_level, formatter) -> Any:
    log_dir = os.path.join(ROOT_LOG_DIR, logger_name)
    Path(log_dir).mkdir(exist_ok=True)
    filepath = os.path.join(
        log_dir,
        time.strftime("%Y-%m-%d", time.localtime()) + ".log"
    )
    file_handler = TimedRotatingFileHandler(
        filepath, when='midnight', backupCount=30, encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    return file_handler

def get_console_handler(log_level, formatter) -> Any:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    return console_handler

def get_logger(logger_name, verbose=False, write_to_file=True):
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    formatter = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
    )
    logger.handlers = []
    logger.addHandler(
        get_console_handler(log_level, formatter)
    )
    logger.addHandler(
        get_error_file_handler(logger_name)
    )
    if write_to_file:
        logger.addHandler(
            get_normal_file_handler(
                logger_name, logging.INFO, formatter
            )
        )
    return logger



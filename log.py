import datetime
import logging
import multiprocessing
import os
import pathlib
import platform
import time
from sys import exit
from typing import Callable

import colorlog.escape_codes

###########################################################
#                         logging                         #
###########################################################
asciiReset = colorlog.escape_codes.escape_codes["reset"]

fileFmtStr = "%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)-5.5s: %(message)s [%(name)s] [%(processName)s(%(process)d)]"
consoleFmtStr = "{}%(asctime)s{} {}%(funcName)s:%(lineno)-3d{} {}%(levelname)-5.5s: %(message)s{}".format(
    "%(bold_purple)s",
    asciiReset,
    "%(purple)s",
    asciiReset,
    "%(log_color)s",
    asciiReset,
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.name = "main"

# hack: 将底层的color暴露出来
COLORS = ["black", "red", "green", "yellow", "blue", "purple", "cyan", "white"]

PREFIXES = [
    # Foreground without prefix
    "",
    "bold_",
    "thin_",
    # Foreground with fg_ prefix
    "fg_",
    "fg_bold_",
    "fg_thin_",
    # Background with bg_ prefix - bold/light works differently
    "bg_",
    "bg_bold_",
]

color_names = {}
for prefix_name in PREFIXES:
    for name in COLORS:
        color_name = prefix_name + name
        color_names[color_name] = color_name

consoleLogFormatter = colorlog.ColoredFormatter(
    consoleFmtStr,
    datefmt="%H:%M:%S",
    reset=True,
    log_colors={
        **color_names,
        **{
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "fg_bold_red",
            "CRITICAL": "fg_bold_red",
        },
    },
    secondary_log_colors={},
    style="%",
)

# 默认创建console输出
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(consoleLogFormatter)
consoleHandler.setLevel(logging.INFO)
logger.addHandler(consoleHandler)


# 文件输出需自行调用，不会默认创建
def add_file_handler(log_directory="logs", logger_name="", deal_with_multiprocessing=False):
    try:
        pathlib.Path(log_directory).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print("创建日志目录logs失败，请确认是否限制了基础的运行权限")
        if platform.system() == "Windows":
            os.system("PAUSE")
        exit(-1)

    # 如果传入了logger名称，则覆盖默认名称
    logger.name = logger_name or logger.name

    # 默认日志文件名以日志名称和当前时间组成
    time_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    log_filename = f"{log_directory}/{logger.name}_{time_str}.log"

    if deal_with_multiprocessing:
        # 为了兼容多进程模式，仅主进程确定日志文件名并存盘，后续其他进程则读取该文件内容作为写日志的目标地址，比如出现很多日志文件
        process_name = multiprocessing.current_process().name

        log_filename_file = ".log.filename"
        if "MainProcess" in process_name:
            log_filename = f"{log_directory}/{logger.name}_{process_name}_{time_str}.log"
            pathlib.Path(log_filename_file).write_text(log_filename, encoding="utf-8")

        for _i in range(3):
            try:
                with open(log_filename_file, encoding="utf-8") as f:
                    log_filename = f.read()
            except Exception as e:
                print(f"读取日志文件名的时候出错了，等待一秒，e={e}")
            if log_filename != "":
                break

            time.sleep(1)

        if log_filename == "":
            print("无法读取到主进程的日志文件名，只能另建一个了~")
            time_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            log_filename = f"{log_directory}/{logger.name}_{process_name}_{time_str}.log"

    # 初始化fileHandler
    fileHandler = logging.FileHandler(log_filename, encoding="utf-8", delay=True)
    fileLogFormatter = logging.Formatter(fileFmtStr)
    fileHandler.setFormatter(fileLogFormatter)
    fileHandler.setLevel(logging.DEBUG)

    logger.addHandler(fileHandler)


def color(color_name):
    return consoleLogFormatter._get_escape_code(consoleLogFormatter.log_colors, color_name)


def with_color(color_name: str, value) -> str:
    return color(color_name) + str(value) + asciiReset


def get_log_func(log_func: Callable, show_log=True) -> Callable:
    if not show_log:
        return logger.debug

    return log_func


if __name__ == "__main__":
    consoleHandler.setLevel(logging.DEBUG)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warn")
    logger.error("error")
    logger.critical("critical")
    logger.exception("exception", exc_info=Exception("测试Exception"))

    for name in color_names:
        print(color(name), name)

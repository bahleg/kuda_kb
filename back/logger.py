from configobj import ConfigObj

import logging
import datetime
import os

def init_logger(activity, level):
    """
    Logger initiazliation.
    Creates file with name <activity>_<datetime>.log
    :param activity: activity name
    :param level: log level. If incorrect, DEBUG will be used
    :return: logger
    """
    logger = logging.getLogger()
    logger.setLevel(10)
    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")

    name = activity + '_' + dt + '.log'
    path =  './logs/'+name
    fh = logging.FileHandler(path)
    could_find_level = False
    try:
        level = logging.getLevelName(level)
        fh.setLevel(level)
        could_find_level = True
    except:
        fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s : %(levelname)s ::: %(message)s')
    formatter_console = logging.Formatter('%(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter_console)
    logger.addHandler(fh)
    logger.addHandler(ch)
    if not could_find_level:
        logger.log(logging.WARNING, 'Wrong log level. Using DEBUG.')
    logger.log(logging.INFO, 'Logger created')
    return logger

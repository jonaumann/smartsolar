import logging
from logging.handlers import RotatingFileHandler
import constants_pv_charging


def setuplog():
    global logger
    logger = logging.getLogger('pv_charge_logger')
    logger.setLevel(logging.INFO)

    fileHandler = RotatingFileHandler(constants_pv_charging.LOG_FILE_NAME, mode='a',
                                      encoding='utf-8', maxBytes=constants_pv_charging.LOG_FILE_MAX_BYTES, backupCount=1)

    fileHandler.setLevel(logging.INFO)

    sysHandler = logging.StreamHandler()
    sysHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')

    fileHandler.setFormatter(formatter)
    sysHandler.setFormatter(formatter)

    logger.addHandler(fileHandler)
    logger.addHandler(sysHandler)


###############################################################################################################
# Logging-Shortcut
###############################################################################################################


def log(value):
    logger.info(value)

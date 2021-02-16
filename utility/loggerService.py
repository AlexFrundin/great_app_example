from utility import Logger
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def loginfo(fileName, description, isDbLog=True):
    try:
        logger.info(description)
    except BaseException as e:
        logger.error(str(e))
        return False


def logerror(fileName, description, isDbLog=True):
    try:
        logger.error(description)
    except BaseException as e:
        logger.error(str(e))
        return False

import os

from dotenv import load_dotenv

from service.logger import get_logger

logger = get_logger()


def is_qa_environment() -> bool:
    """
    Tells us if we are in a QA environmental context
    :return: bool
    """
    load_dotenv()
    result = os.getenv("IS_QA", "False").lower()
    logger.info(f"is_qa_environment: {result}")
    return result == "true"

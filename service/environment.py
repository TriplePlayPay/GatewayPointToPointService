import os


def is_qa_environment() -> bool:
    """
    Tells us if we are in a QA environmental context
    :return: bool
    """
    return os.getenv("IS_QA", "False").lower() == 'true'
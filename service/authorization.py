import aiohttp

from sanic import json, Request

from service.logger import get_logger
from service.models import EPXCredentials

logger = get_logger()


class CredentialingError(Exception):
    """
    Contains authorization error context
    """
    pass


def get_api_key_from_http_request(request: Request) -> str:
    """
    Returns the API Key from a given request
    :param request:
    :return:
    """
    def remove_bearer_prefix_case_insensitive(s):
        prefix = "bearer "
        if s.lower().startswith(prefix):
            return s[len(prefix) :]
        return s

    api_key = remove_bearer_prefix_case_insensitive(
        request.headers.get("Authorization")
    )
    logger.info(f"api_key value gotten from authorization: {api_key}")
    return api_key


async def get_credentials_from_api_key(api_key: str, is_qa: bool = False) -> EPXCredentials:
    """
    Authorizes a key against our primary server.

    Returns a boolean to let us know if the caller is authorized or not.

    :param api_key: str
    :param is_qa: bool
    :return: bool
    """

    data = {
        "auth_key": api_key,
        "qa": is_qa
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    logger.info(f"Submitting data for authorization: {data}")
    # url = 'http://localhost/passthrough' if is_qa else 'https://tripleplaypay.com/passthrough'
    url = 'https://tripleplaypay.com/passthrough'

    # use async ClientSession to POST
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, json=data) as response:

            if response.status != 200:
                raise CredentialingError("The passthrough request was not successful.")

            the_json = await response.json()

            is_authorized = the_json.get("authorized", False)
            if not is_authorized:
                raise CredentialingError("The merchant is not authorized to perform this action.")

            credentials = EPXCredentials(
                MERCH_NBR=the_json.get("MERCH_NBR"),
                TERMINAL_NBR=the_json.get("TERMINAL_NBR"),
                CUST_NBR=the_json.get("CUST_NBR"),
                DBA_NBR=the_json.get("DBA_NBR")
            )

            if credentials.MERCH_NBR == 0:
                raise CredentialingError("The merchant exists but is not authorized on EPX.")

            return credentials

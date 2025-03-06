"""
This calls our central and cryptography service
"""
from typing import Dict, Any
from dataclasses import asdict

from service.json_util import ignore_properties
from service.logger import get_logger
from service.courier import CourierRequest
from service.models import TerminalRegistryParameters, RemoteKeyInjectionParameters, InitialRemoteKeyInjectionParameters


logger = get_logger()


async def register_terminal(
    terminal_parameters: TerminalRegistryParameters,
    auth_key: str,
    is_qa: bool = False
) -> Dict[str, Any]:
    """
    Makes an API call to get the terminal registered with our
    centralized system, so it can get the right key to be able
    to get and verify the IPEK.

    :param terminal_parameters: TerminalRegistryParameters
    :param auth_key: str
    :param is_qa: bool
    :return: Dict[str, Any]
    """
    url = "http://localhost/api/ipek" if is_qa else "https://tripleplaypay.com/api/ipek"
    courier_request = CourierRequest(
        mode="POST",
        url=url,
        body=asdict(terminal_parameters),
        headers={"Authorization": f"Bearer {auth_key}"},
    )
    return await courier_request.send()


async def get_key_for_remote_key_injection(
    rki_parameters: RemoteKeyInjectionParameters,
    is_qa: bool = False
) -> Dict[str, Any]:
    """
    This gets a key for remote key injection as
    an encrypted parameter the terminal will have
    to decrypt.

    :param rki_parameters: RemoteKeyInjectionParameters
    :param is_qa: bool
    :return: Dict[str, Any]
    """
    url = "http://localhost:9001/api/ipek" if is_qa else "https://cryptography.tripleplaypay.com/api/ipek"
    courier_request = CourierRequest(
        mode="POST",
        url=url,
        body=asdict(rki_parameters),
    )
    return await courier_request.send()


async def get_remote_key_injection_parameters_from_terminal_id(
    rki_parameters: InitialRemoteKeyInjectionParameters,
    auth_key: str,
    is_qa: bool = False
) -> RemoteKeyInjectionParameters:
    """
    This gets a key for remote key injection as
    an encrypted parameter the terminal will have
    to decrypt.

    :param rki_parameters: RemoteKeyInjectionParameters
    :param auth_key: str
    :param is_qa: bool
    :return: RemoteKeyInjectionParameters
    """
    if is_qa:
        url = f"http://localhost/api/ipek/terminal/{rki_parameters.terminal_id}"
    else:
        url = f"https://tripleplaypay.com/api/ipek/terminal/{rki_parameters.terminal_id}"

    # Send the request
    courier_request = CourierRequest(
        mode="GET",
        url=url,
        headers={"Authorization": f"Bearer {auth_key}"},
    )

    # Get the results
    results = await courier_request.send()

    logger.info(f"Results from get terminal: {results}")

    # arrange the message
    the_message = results.get("message")
    the_message["nonce"] = rki_parameters.nonce
    the_message["signature"] = rki_parameters.signature

    # Return the relevant message
    return ignore_properties(RemoteKeyInjectionParameters, the_message)

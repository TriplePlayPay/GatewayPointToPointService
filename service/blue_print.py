from dataclasses import asdict

from sanic import json, Request, SanicException, Blueprint
from sanic.response import JSONResponse

from service.logger import get_logger
from service.models import TransactionRequest
from service.authorization import get_api_key_from_http_request, get_credentials_from_api_key
from service.json_util import ignore_properties
from service.epx import EPXProcessor

logger = get_logger()

bp = Blueprint("PointToPoint", url_prefix="/p2pe")


@bp.post("/transaction")
async def transaction(request: Request) -> JSONResponse:
    """
    Using a dedicated request, call EPX as a pass through.
    :param request: Request
    :return: JSONResponse
    """

    is_qa = True
    logger.info(f"Transaction called with the following parameters: {request.json}")
    request_input = ignore_properties(TransactionRequest, request.json)

    # Authorize the request
    api_key = get_api_key_from_http_request(request)
    try:
        credentials = await get_credentials_from_api_key(api_key, is_qa)
    except Exception:
        logger.exception("Exception getting credentials from the provided API key")
        raise SanicException("Not authorized to perform this action.", status_code=401)

    try:
        # Send the request to the processor
        processor = EPXProcessor(credentials, is_qa)
        result = await processor.charge(request_input)
    except Exception:
        logger.exception("Exception while attempting to process")
        raise SanicException("Unable to successfully complete transaction.", status_code=400)

    # Return the result
    return json(asdict(result))

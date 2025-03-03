import arrow
from typing import Dict, Any
from dataclasses import asdict
import urllib.parse as parse
import uuid
from service.logger import get_logger
from service.courier import CourierRequest
from service.json_util import ignore_properties
from service.models import TransactionRequest, TransactionResponse, EPXCredentials

logger = get_logger()

EPX_TIME_ZONE = "US/Eastern"


class EPXProcessor:
    """
    Processes EPX specific transactions
    """

    def __init__(
            self,
            epx_credentials: EPXCredentials,
            qa=False,
    ):
        self.qa = qa
        self.url = "https://secure.epx.com"
        self.creds = asdict(epx_credentials)
        if self.qa:
            self.url = "https://secure.epxuap.com"
        self.reference = str(uuid.uuid4())
        self.tranid = arrow.now(EPX_TIME_ZONE).format("MMDDHHmmss")
        self.batchid = arrow.now(EPX_TIME_ZONE).format("YYYYMMDD")
        self.is_web_request_successful = False

    async def charge(self, transaction_request: TransactionRequest) -> TransactionResponse:
        """
        The sale transaction is an authorization and capture within the same transaction. Because of
        this, the authorization is immediately captured by the EPX platform so no additional
        transaction is required to capture the authorization. If the sale is approved, the transaction will
        close and settle during the next batch close time for funding to take place.
        :param transaction_request:
        :return: TransactionResponse
        """

        transmission_body = asdict(transaction_request)
        transmission_body['BATCH_ID'] = self.batchid
        transmission_body['TRAN_NBR'] = self.tranid

        final_transmission_body = {}

        # Avoid sending None as a string value
        for key, value in transmission_body.items():
            if value is not None:
                final_transmission_body[key] = value

        return await self.transmit(final_transmission_body)

    @staticmethod
    def format_response(meta: Dict[str, Any]) -> Dict[str, Any]:
        r = meta
        try:
            return {
                i["@KEY"]: i.get("#text", "") for i in r["RESPONSE"]["FIELDS"]["FIELD"]
            }
        except KeyError:
            raise

    async def transmit(self, body, mode="POST") -> TransactionResponse:
        """
        Use the Courier package to send the request to EPX
        :param body:
        :param mode:
        :return:
        """
        body.update(self.creds)
        body = parse.urlencode(body)
        logger.info(f"Submitting request body to EPX: {body}")

        courier_request = CourierRequest(
            mode=mode,
            url=self.url,
            body=body,
            headers={"Content-Type": "text/xml"},
            is_xml=True,
        )

        # Send API Request
        api_response = await courier_request.send()

        # format the response
        logger.info(f"Raw api_response from EPX: {api_response}")
        transaction_response = EPXProcessor.format_response(api_response)

        # reply with all known properties
        logger.info(f"transaction_response from us: {transaction_response}")
        return ignore_properties(TransactionResponse, transaction_response)

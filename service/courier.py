import json
from typing import Any, Dict, Literal

import aiohttp
import xmltodict

from service.json_util import UUIDEncoder
from service.logger import get_logger

logger = get_logger()


# Use the same values for the Literal type hint
ALLOWED_VERBS = ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
HTTPVerb = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]


class CourierHTTPRequestError(Exception):
    """
    Deals with Courier-Specific Errors
    """
    pass


class CourierRequest:
    """
    The provided code is a Python class that defines a Request for making HTTP requests.
    The Request class uses the urllib3 library primarily, but falls back to the requests library if an error occurs.
    """

    def __init__(
        self,
        url=None,
        body=None,
        fields=None,
        mode: HTTPVerb = None,
        headers=None,
        is_xml=False
    ):
        """
        Initializes a new instance of the CourierRequest class.

        Args:
            url (str): The URL for the HTTP request.
            body (str | dict[str, Any]): The body of the HTTP request.
            fields (dict): The fields of the HTTP request.
            mode (str): The HTTP method for the request.
            headers (dict): The headers for the HTTP request.
            is_xml (bool): A flag indicating whether the request is XML.
        """
        self.errors = []
        self.failures = []

        self.url = url
        self.body = body
        self.fields = fields
        self.mode = mode
        self.headers = headers if headers else {}
        self.is_xml = is_xml

        if not self.url:
            self.errors.append("No url parameter")

        if not self.mode:
            self.errors.append("No mode parameter")

        if self.mode.upper() not in ALLOWED_VERBS:
            self.errors.append(f"Invalid HTTP verb provided: {self.mode}")

        if self.mode.upper() == "POST" and not self.body:
            self.errors.append("Post request called with no body")

        self.__error_check()

    @property
    def base(self) -> Dict:
        """
        Represents a base HTTP request parameter set
        """
        return {"url": self.url, "method": self.mode, "headers": self.headers}

    @property
    def request(self) -> Dict:
        """
        Represents a request body
        """
        base = self.base
        if self.body:
            if self.is_xml:
                base["data"] = json.loads(json.dumps(self.body, cls=UUIDEncoder))
            else:
                base["json"] = json.loads(json.dumps(self.body, cls=UUIDEncoder))
        if self.fields:
            base["fields"] = self.fields

        return base

    @property
    def requests_request(self) -> Dict:
        """
        In the event urllib3 requests fail, we use the requests library to send a backup.
        """
        base = self.base
        if self.body:
            base["json"] = json.loads(json.dumps(self.body, cls=UUIDEncoder))

        return base

    def __error_check(self) -> None:
        """
        Checks the contents of the `errors` property to see if we have any.

        It will raise an exception if so.
        """
        if len(self.errors) > 0:
            raise CourierHTTPRequestError("HTTP Request Errors Present", self.errors)

    async def send(self) -> Any | None:
        """
        Sends out the request, handling exceptions along the way.
        """
        logger.info(f"About to send out request: {self.request}")

        try:
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as client:
                client_response = await client.request(**self.request)
                # disable MIME type checks on JSON responses for now
                response = (
                    await client_response.text("utf-8")
                    if self.is_xml
                    else await client_response.json(content_type=None)
                )
        except aiohttp.ClientConnectionError:
            """
            It failed specifically to connect to the endpoint that was called
            """
            logger.exception(
                f"ClientConnectionError thrown with request: {self.request}"
            )
            raise CourierHTTPRequestError(f"ClientConnectionError with request made to: {self.url}")
        except aiohttp.ClientError:
            """
            This is here to just catch any other exception which could occur.
            """
            logger.exception(f"ClientError thrown with request: {self.request}")
            raise CourierHTTPRequestError(f"ClientError with request made to: {self.url}")

        # If it succeeded in the first block
        if response:
            if self.is_xml:
                return xmltodict.parse(response)
            logger.info(f"returning {response} from Request.send")
            return response

        raise CourierHTTPRequestError(f"No response from request made to: {self.url}")

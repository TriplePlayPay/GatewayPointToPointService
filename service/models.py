from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EPXCredentials:
    """
    Response gotten from our passthrough api request
    """
    CUST_NBR: int
    MERCH_NBR: int
    DBA_NBR: int
    TERMINAL_NBR: int


@dataclass
class TransactionRequest:
    """
    Models a transaction request payload based on the EPX EMV documentation.
    """
    # Required Fields
    AMOUNT: str
    TRAN_TYPE: str
    TRACK_DATA: str
    CURRENCY_CODE: str

    # Optional Fields
    CARD_ENT_METH: Optional[str] = None
    E2EE: Optional[str] = None
    EMV_DATA: Optional[str] = None
    PIN_BLK: Optional[str] = None
    CARD_ID: Optional[str] = None
    INDUSTRY_TYPE: Optional[str] = None
    CHIP_CONDITION_CODE: Optional[str] = None
    REASON_CODE: Optional[str] = None
    PAYMENT_INITIATION_CHANNEL: Optional[str] = None
    MAC: Optional[str] = None
    ZIP_CODE: Optional[str] = None


@dataclass
class TransactionResponse:
    """
    Models a transaction response payload from the processor based on the EPX EMV documentation.
    """

    # Often present or required by the system:
    AUTH_RESP: str
    AUTH_RESP_TEXT: str

    # Other fields can be optionally present depending on the issuer and environment
    MSG_VERSION: Optional[str] = None
    CUST_NBR: Optional[str] = None
    MERCH_NBR: Optional[str] = None
    DBA_NBR: Optional[str] = None
    TERMINAL_NBR: Optional[str] = None
    TRAN_TYPE: Optional[str] = None
    BATCH_ID: Optional[str] = None
    TRAN_NBR: Optional[str] = None
    LOCAL_DATE: Optional[str] = None
    LOCAL_TIME: Optional[str] = None
    AUTH_GUID: Optional[str] = None
    AUTH_CODE: Optional[str] = None
    AUTH_CARD_TYPE: Optional[str] = None
    AUTH_TRAN_DATE_GMT: Optional[str] = None
    AUTH_AMOUNT_REQUESTED: Optional[str] = None
    AUTH_AMOUNT: Optional[str] = None
    AUTH_CURRENCY_CODE: Optional[str] = None
    NETWORK_RESPONSE: Optional[str] = None
    AUTH_CARD_COUNTRY_CODE: Optional[str] = None
    AUTH_CARD_COUNTRY_NAME: Optional[str] = None
    AUTH_CARD_CURRENCY_CODE: Optional[str] = None
    AUTH_CARD_CURRENCY_NAME: Optional[str] = None
    AUTH_CARD_B: Optional[str] = None
    AUTH_CARD_A: Optional[str] = None
    AUTH_CARD_C: Optional[str] = None
    AUTH_MASKED_ACCOUNT_NBR: Optional[str] = None
    AUTH_CARD_K: Optional[str] = None
    AUTH_CARD_L: Optional[str] = None
    AUTH_EMV_DATA: Optional[str] = None


@dataclass
class TerminalRegistryParameters:
    terminal_id: str
    public_key: str


@dataclass
class InitialRemoteKeyInjectionParameters:
    terminal_id: str
    nonce: str
    signature: str


@dataclass
class RemoteKeyInjectionParameters:
    terminal_id: str
    nonce: str
    signature: str
    public_key: str
    full_ksn: str

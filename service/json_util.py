import json
from dataclasses import fields, is_dataclass, asdict
from json import JSONEncoder
import decimal
from datetime import date
from datetime import datetime
from typing import TypeVar, Type, Any
from uuid import UUID

_T = TypeVar("_T")


def ignore_properties(cls: Type[_T], dict_: Any) -> _T:
    """omits extra fields like @JsonIgnoreProperties(ignoreUnknown = true)"""
    if isinstance(dict_, cls):
        return dict_  # noqa
    class_fields = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in dict_.items() if k in class_fields}
    return cls(**filtered)


class EnhancedJSONEncoder(JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


class UUIDEncoder(JSONEncoder):
    """
    Enables the decoding of UUID values.

    Useful for parsing asyncpg Record entries.
    """

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

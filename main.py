from typing import (
    Any, Dict, Generic, Optional, TypeVar, Union, get_origin
)

from pydantic import BaseModel as OriginalBaseModel
from pydantic import root_validator
from pydantic.json import ENCODERS_BY_TYPE

_T = TypeVar("T")
_V = TypeVar("V")


class Result(Generic[_T]):
    """Result type in order to correctly handle None or Any value."""
    __value: Optional[_T]
    
    def __init__(self, value: Optional[_T] = None) -> None:
        self.__value = value

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "Result(%s)" % repr(self.__value)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v if isinstance(v, cls) else Result(v)
    
    @property
    def is_none(self) -> bool:
        """Return True if Result value is None."""
        return self.__value is None
      
    def unwrap(self, *, error_msg: str = None) -> _T:
        """Unwrap the Result value if it's not None, otherwise a
        ValueError will be raised with the appropriate error_msg.
        """
        if self.__value is not None:
            raise ValueError(error_msg or "Value is None.")
        return self.__value
    
    def unwrap_or(self, variant: _V, /) -> Union[_T, _V]:
        """Unwrap the Result value if it's not None,
        otherwise it will return the variant you passed.
        """
        if variant is None:
            raise ValueError("Variant should not be type 'NoneType'.")
        return self.__value if self.__value is not None else variant
        

class BaseModel(OriginalBaseModel):
    @root_validator(pre=True)
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        model_schema = cls.schema()
        fields = _get_defaults(model_schema)
        fields.update(
            _get_required_result_fields(cls.__annotations__, model_schema)
        )
        fields.update(values)
        return {
            field: Result(value) if _is_result_type(cls.__annotations__.get(field, None))
            and not isinstance(value, Result) else value for field, value in fields.items()
        }
    

def _is_result_type(type_: type) -> bool:
    origin_type = get_origin(type_)
    result_type = (
        type(type_) if type_ is None else
        type_ if origin_type is Union else
        origin_type or type_
    )
    return issubclass(Result, origin_type)


def _get_defaults(schema: Dict[str, Any]) -> Dict[str, Any]:
    properties = schema.get("properties", {})
    if not properties:
        return {}
    return {
        k: properties[k]["default"] for k in properties if "default" in properties[k]
    }


def _get_required_result_fields(annotations: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, "Result"]:
    properties = schema.get("properties", {})
    if not properties:
        return {}
    return {
        k: Result() for k in properties if k in schema.get("required", [])
        or "default" not in properties[k] and _is_result_type(annotations[k])
    }


ENCODERS_BY_TYPE[Result] = lambda v: v

from typing import (Any, Dict, Generic, Optional, Type, TypeVar, Union,
                    get_origin)
from pydantic import BaseModel as OriginalBaseModel
from pydantic import create_model, root_validator
from pydantic.fields import ModelField
from pydantic.json import ENCODERS_BY_TYPE
from pydantic.typing import is_none_type

_T = TypeVar("_T")
_V = TypeVar("_V")
__all__ = "BaseModel", "Result"


class Result(Generic[_T]):
    """Result type in order to correctly handle None or Any value."""
    __value: Optional[_T]
    
    def __init__(self, value: Optional[_T] = None) -> None:
        self.__value = value

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, repr(self.__value),)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, field: ModelField) -> "Result[_T]":
        result_type = field.outer_type_.__args__[0]
        field_name = field.name
        if field_name.startswith("_"):
            field_name = field_name[1:]
        if field_name.endswith("_"):
            field_name = field_name[:-1]
        if isinstance(v, cls):
            if v.is_none:
                return v
            _model = _create_result_model(
                field_name, v.unwrap(), result_type
            )
            return cls(getattr(_model, field_name))
        if v is None:
            return cls(v)
        _model = _create_result_model(field_name, v, result_type)
        return cls(getattr(_model, field_name))
        
    @property
    def is_none(self) -> bool:
        """Return True if Result value is None."""
        return self.__value is None
      
    def unwrap(self, *, error_msg: str = None) -> _T:
        """Unwrap the Result value if it's not None, otherwise a
        ValueError will be raised with the appropriate error_msg.
        """
        if self.__value is None:
            raise ValueError(
                error_msg if error_msg is not None else "Value is None."
            )
        return self.__value
    
    def unwrap_or(self, variant: _V, /) -> Union[_T, _V]:
        """Unwrap the Result value if it's not None,
        otherwise it will return the variant you passed.
        """
        if variant is None:
            raise TypeError("Variant should not be type 'NoneType'.")
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
    

def _is_result_type(type_: Type[Any]) -> bool:
    if type_ is None or is_none_type(type_):
        return False
    origin = get_origin(type_)
    if origin is None:
        return False
    return origin is Result


def _get_defaults(schema: Dict[str, Any]) -> Dict[str, Any]:
    properties = schema.get("properties", {})
    if not properties:
        return {}
    return {
        k: properties[k]["default"] for k in properties
        if "default" in properties[k]
    }


def _get_required_result_fields(annotations: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, "Result"]:
    properties = schema.get("properties", {})
    if not properties:
        return {}
    return {
        k: Result() for k in properties if k in schema.get("required", [])
        or "default" not in properties[k] and _is_result_type(annotations[k])
    }


def _create_result_model(field_name: str, value: Any, type_: Type[Any]) -> "BaseModel":
    return create_model(
        "ResultModel", __base__=BaseModel,
        **{field_name: (type_, value,)}
    )()


ENCODERS_BY_TYPE[Result] = lambda v: None if v.is_none else v.unwrap()

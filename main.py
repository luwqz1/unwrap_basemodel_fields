from typing import Any, Dict, Generic, Optional, TypeVar, Union, get_origin

from pydantic import BaseModel as OriginalBaseModel
from pydantic import root_validator, validator

T = TypeVar("T")
V = TypeVar("V")


class Result(Generic[T]):
    """Result type in order to correctly handle None or Any value."""
    __value: Optional[T]
    
    def __init__(self, value: Optional[T] = None) -> None:
        self.__value = value

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
      
    def unwrap(self, *, error_msg: str = None) -> T:
        """Unwrap the Result value if it's not None, otherwise a
        ValueError will be raised with the appropriate error_msg.
        """
        if self.__value is not None:
            raise ValueError(error_msg or "Value is None.")
        return self.__value
    
    def unwrap_or(self, variant: V, /) -> Union[T, V]:
        """Unwrap the Result value if it's not None,
        otherwise it will return the variant you passed.
        """
        if variant is None:
            raise ValueError("Variant should not be type 'NoneType'.")
        return self.__value if self.__value is not None else variant
        

class BaseModel(OriginalBaseModel):
    class Config:
        validate_all = True

    @root_validator(pre=True)
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        return {
            field: Result() if _is_result_type(
                cls.__annotations__.get(field, None)
            )
            and value is None else value
            for field, value in values.items()
        }
    
    @validator("*", pre=True)
    def validate_default_fields(cls, v, field):
        if not field.required and _is_result_type(
            cls.__annotations__.get(field.name, None)
        ):
            return Result(v)
        return v


def _is_result_type(type_: type) -> bool:
    origin_type = get_origin(type_)
    
    if origin_type is Union:
        origin_type = type_
    else:
        origin_type = (
            type(type_) if type_ is None
            else origin_type or type_
        )
    
    return issubclass(Result, origin_type)

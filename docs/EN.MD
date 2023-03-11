# Welcome to the unwrapper documentation!

So module **unwrapper** provides only two classes: `BaseModel`, `Result`. The **BaseModel** class is slightly redesigned. The **root_validator** method class for the **Result** type has been changed in it. The **Result** class is the same `Optional`, its behavior is exactly the same, but the object itself is a set of several methods and one property.

# Class Result

```python
class Result(Generic[_T]):
    def __init__(self, value: Optional[_T] = None) -> None: ...
```

**Class methods:**
- [**unwrap**](#unwrap)
- [**unwrap_or**](#unwrap_or)

**Class properties:**
- [**is_none**](#is_none)

# Examples of how to use the methods

### unwrap

```python
def unwrap(self, *, error_msg: str = None) -> _T: ...
```

```python
from unwrapper import Result

r = Result("Hello!")
print(r.unwrap())
#> Hello!
```
**This method unwrap the value, if it is not None, then `unwrap` will return it, otherwise it will raise an exception `ValueError`. In this example, the value was not `None`, so it was able to return it, but let's see when the value is `None`.**

```python
from unwrapper import Result

r = Result()
print(r.unwrap())
#> ValueError: Value is None.
```

**It is worth noting that unwrap has a named argument `error_msg` of type `str` that takes an error message. By default its value is `None`, so the error message will be ``Value is None``. __Parameter must be specified with its name.__**

```python
from unwrapper import Result

r = Result(input("Enter your name or press enter to skip: ") or None)
print("Hello,", r.unwrap(error_msg="You are anonymous!") + "!")
#> ValueError: You are anonymous!
```

### unwrap_or

```python
def unwrap_or(self, variant: _V, /) -> Union[_T, _V]: ...
```

**Same as `unwrap`, only `unwrap_or` does not throw an exception, but returns a value (called `variant`) that was passed to it as a parameter, and it can be of any type except `None`, otherwise there will be an error. A parameter via its name cannot be specified.**

```python
from unwrapper import unwrap

r = Result(True)
print("True!" if r.unwrap_or(False) else "False...")
#> True!
```

**Now let's get the value from `variant`**

```python 
from uuid import uuid4
from unwrapper import Result

r = Result()
print("Your id:", r.unwrap_or(uuid4().int << 64))
#> Your id: 3806679325074015802
```

# Examples of using properties

### is_none

```python
@property
def is_none(self) -> bool: ...
```

**Property that checks the value, if it is `None` it returns `True`, otherwise `False`**

```python
from unwrapper import Result

r = Result({"age": 25})
print(r.is_none)
#> False
```

**Simple example, if you don't need an exception and another variant value**

```python
from unwrapper import Result

r = Result()
print(None if r.is_none else r.unwrap())
#> None
```

# Example Result in type hinting

Since `Result` inherits the `Generic` class from the `typing` module, you can use it by specifying a generic. The generic includes one parameter.

```python
from unwrapper import Result

def print_name(name: Result[str]) -> None:
    print(name.unwrap_or("What's your name??"))
```

**It will be wrong if you specify `Result[Optional[Any]]` or `Result[Any | None]`, because the `unwrap` and `unwrap_or` methods cannot return `None`.**

# Work Result with BaseModel

For `BaseModel` type `Result` works like `Optional`, for example:

```python
from unwrapper import BaseModel, Result

class User(BaseModel):
    name: Result[str]

print(User())
#> User(name=Result(None))
```

__I.e., if a field has no default value and the field with the corresponding value was not passed to the model, then the default value `Result(None)` is generated.__

There are 2 ways to specify a default value for fields of type `Result`:

```python
from unwrapper import BaseModel, Result

class Item(BaseModel):
    cost: int
    title: Result[str] = Result("Unknown item")


class ServerResponse(BaseModel):
    response_code: int
    items: Result[list[Item]] = []

response = {
    "items": [{"cost": 1500}],
    "response_code": 200,
}
print(ServerResponse(**response))
#> ServerResponse(response_code=200, items=Result([Item(cost=1500, title=Result('Unknown item'))]))
print(ServerResponse(response_code=404))
#> ServerResponse(response_code=404, items=Result([]))
```
> **Note**: __`Pydantic` also strictly refers to the type passed to `Result`. Its type validation is fully preserved.__

__It is better, of course, to specify value specifically with `Result`, so linters do not swear on type mismatch, but it is possible to specify without `Result`. A similar situation is when values are passed to the model, it is possible with or without Result, but this is already done so that values from json are passed or from some data, here is an example:__

```python
from unwrapper import BaseModel, Result

class Member(BaseModel):
    nickname: str
    level: int
    bio: Result[str]

class Clan(BaseModel):
    title: str
    creator: Member
    members: list[Member]
    description: Result[str]

raw_obj = '''{
    "title": "Strong",
    "creator": {
        "nickname": "Lord111",
        "level": 79,
        "bio": "I love my clan!!!"
    },
    "members": [
        {
            "nickname": "Lord11",
            "level": 79,
            "bio": "I love my clan!!!"
        },
        {
            "nickname": "Ms.Archer",
            "level": 55, 
            "bio": null
        }
    ], 
    "description": null
}'''
clan = Clan.parse_raw(raw_obj)
print(clan)
"""> Clan(
    title='Strong', creator=Member(nickname='Lord111', level=79, bio=Result('I love my clan!!!')),
    members=[Member(nickname='Lord11', level=79, bio=Result('I love my clan!!!')), Member(nickname='Ms.Archer', level=55, bio=Result(None))],
    description=Result(None)
)
"""
print(
    Clan(
        title=clan.title, creator=clan.creator,
        members=[], description=None
    )
)
"""> Clan(
    title='Strong', creator=Member(nickname='Lord111', level=79, bio=Result('I love my clan!!!')),
    members=[], description=Result(None)
)
"""
```
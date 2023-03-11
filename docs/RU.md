#  Добро пожаловать в документацию про unwrapper!

Итак, модуль **unwrapper** предоставляет всего лишь два класса: `BaseModel`, `Result`. Класс **BaseModel** немного переделан. В нем изменен класс метод **root_validator** для типа **Result**. Класс **Result** — ***это тот же*** `Optional`, ***его поведение точно такое же, но сам объект представляет набор из нескольких методов и одного свойства.***

# Класс Result

```python
class Result(Generic[_T]):
    def __init__(self, value: Optional[_T] = None) -> None: ...
```

**Методы класса:**
- [**unwrap**](#unwrap)
- [**unwrap_or**](#unwrap_or)

**Свойства класса:**
- [**is_none**](#is_none)

# Примеры использования методов

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
**Данный метод разварачивает значение, если оно не None, тогда `unwrap` вернет его, иначе вызовет исключение `ValueError`. В данном примере значение оказалось не `None`, поэтому он его смог вернуть, но давайте посмотрим, когда значение бывает `None`.**

```python
from unwrapper import Result

r = Result()
print(r.unwrap())
#> ValueError: Value is None.
```

**Стоит отметить, что у unwrap есть именованный аргумент `error_msg` типа `str`, который принимает сообщение ошибки. По дефолту его значение `None`, поэтому сообщение ошибки будет `"Value is None"`. __Параметр нужно обязательно указывать через его имя.__** 

```python
from unwrapper import Result

r = Result(input("Укажите ваше имя, либо нажмите enter, чтобы пропустить: ") or None)
print("Привет,", r.unwrap(error_msg="Вы аноним!") + "!")
#> ValueError: Вы аноним!
```

### unwrap_or

```python
def unwrap_or(self, variant: _V, /) -> Union[_T, _V]: ...
```

**То же самое, что и `unwrap`, но только `unwrap_or` не вызывает исключение, а возвращает значение (так называемый `variant`), которое ему передали в качестве параметра, причем оно может быть любого типа, кроме `None`, иначе будет будет ошибка. Параметр через его имя нельзя указывать.**

```python
from unwrapper import unwrap

r = Result(True)
print("Правда!" if r.unwrap_or(False) else "Ложь...")
#> Правда!
```

**Теперь получим значение из `variant`**

```python 
from uuid import uuid4
from unwrapper import Result

r = Result()
print("Ваш айди:", r.unwrap_or(uuid4().int << 64))
#> Ваш айди: 3806679325074015802
```

# Примеры использования свойств

### is_none

```python
@property
def is_none(self) -> bool: ...
```

**Свойство, которое проверяет значение, если оно `None`, то возвращает `True`, иначе `False`**

```python
from unwrapper import Result

r = Result({"age": 25})
print(r.is_none)
#> False
```

**Простой пример, если не нужно исключение и другой вариант значения**

```python
from unwrapper import Result

r = Result()
print(None if r.is_none else r.unwrap())
#> None
```

# Пример Result в типизации

Так как `Result` наследует класс `Generic` из модуля `typing`, его можно использовать, указывая дженерик. В дженерик входит один параметр.

```python
from unwrapper import Result

def print_name(name: Result[str]) -> None:
    print(name.unwrap_or("Как тебя зовут??"))
```

**Будет неправильно, если вы укажите `Result[Optional[Any]]` или `Result[Any | None]`, потому что методы `unwrap` и `unwrap_or` не могут вернуть `None`.**

# Работа Result с BaseModel

Для `BaseModel` тип `Result` работает как `Optional`, например:

```python
from unwrapper import BaseModel, Result

class User(BaseModel):
    name: Result[str]

print(User())
#> User(name=Result(None))
```

__Т.е, если у поля нет дефолтного значения и поле с соответствующим  значением не было передано в модель, тогда генерируется дефолтное значение `Result(None)`.__

Указывать дефолтное значение для полей типа `Result` можно 2-мя способами:

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
> **Примечание**: __`Pydantic` также строго относится к типу, который передали в `Result`. Его валидация типов полностью сохранена.__

__Лучше, конечно, указывать значение конкретно с `Result`, чтобы линтеры не ругались на несоответсвие типов, но возможность указывать без `Result` есть. Аналогичная ситуация, когда значения передаются в модель, можно с Result, а можно и без него, но это уже сделано для того, чтобы значения из json передавались или из какой-то data, вот пример:__

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

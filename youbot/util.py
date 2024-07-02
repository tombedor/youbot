from typing import Callable, Generic, Optional, Type, TypeVar
from toolz import curry


T = TypeVar("T")
U = TypeVar("U")


class Maybe(Generic[T]):
    def __init__(self, value: Optional[T] = None):
        self._value = value

    @property
    def value(self) -> Optional[T]:
        return self._value

    def is_some(self) -> bool:
        return self._value is not None

    def is_nothing(self) -> bool:
        return self._value is None

    def map(self, func: Callable[[T], U]) -> "Maybe[U]":
        if self.is_some():
            return Some(func(self._value))  # type: ignore
        else:
            return Nothing()  # type: ignore

    def flat_map(self, func: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        if self.is_some():
            return func(self._value)  # type: ignore
        else:
            return Nothing()  # type: ignore

    def __repr__(self) -> str:
        if self.is_some():
            return f"Some({self._value})"
        else:
            return "Nothing"


class Some(Maybe[T]):
    def __init__(self, value: T):
        super().__init__(value)


class Nothing(Maybe[None]):
    def __init__(self):
        super().__init__(None)


@curry
def maybe_map(func: Callable[[T], U], container: Maybe[T]) -> Maybe[U]:
    return container.map(func)


@curry
def assert_type(expected_type: Type, value: T) -> T:
    if not isinstance(value, expected_type):
        raise ValueError(f"Expected {expected_type} but got {type(value)}")
    else:
        return value


def debug(value: T) -> T:
    import pdb

    pdb.set_trace()
    return value


def debug_log(value: T) -> T:
    import traceback

    traceback.print_stack()
    print(f"CURRENT VALUE: {value}")
    return value

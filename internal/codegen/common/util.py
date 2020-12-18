from typing import Generic, TypeVar, List, Optional, Callable

T = TypeVar('T')
R = TypeVar('R')
P0 = TypeVar('P0')
P1 = TypeVar('P1')


class State(Generic[T]):
    def __init__(self, state: T):
        self._state = state

    def state(self) -> T:
        return self._state

    def forward(self, state: T) -> T:
        self._state = state

        return state


class ListCollection(Generic[T]):
    def __init__(self, elements: List[T]):
        self._elements = elements

    def count(self) -> int:
        return len(self._elements)

    def elements(self) -> List[T]:
        return self._copy_elements()

    def is_empty(self) -> bool:
        return self.count() == 0

    def first(self) -> Optional[T]:
        return self._elements[0] if not self.is_empty() else None

    def last(self) -> Optional[T]:
        return self._elements[-1] if not self.is_empty() else None

    def head(self) -> Optional[T]:
        return self.first()

    def tail(self) -> 'ListCollection[T]':
        return ListCollection(self._elements[1:])

    def reverse(self) -> 'ListCollection[T]':
        return ListCollection(self._elements[::-1])

    def map(self, fn: Callable[[T], R]) -> 'ListCollection[R]':
        return ListCollection([fn(elem) for elem in self._elements])

    def fold(self, initial_state: R, fn: Callable[[R, T], R]) -> 'ListCollection[R]':
        state = State(initial_state)
        return self.map(lambda elem: state.forward(fn(state.state(), elem)))

    def fold_right(self, initial_state: R, fn: Callable[[R, T], R]) -> 'ListCollection[R]':
        return self.reverse().fold(initial_state, fn).reverse()

    def reduce(self, initial_state: R, fn: Callable[[R, T], R]) -> R:
        return self.fold(initial_state, fn).last()

    def reduce_right(self, initial_state: R, fn: Callable[[R, T], R]) -> R:
        return self.fold_right(initial_state, fn).first()

    def filter(self, fn: Callable[[T], bool]) -> 'ListCollection[T]':
        return ListCollection(self.reduce([], lambda state, elem: [*state, elem] if fn(elem) else state))

    def single(self, fn: Callable[[T], bool]) -> Optional[T]:
        for elem in self._elements:
            if fn(elem):
                return elem

        return None

    def _copy_elements(self) -> List[T]:
        return self._elements.copy()

    def __str__(self):
        return self._elements.__str__()

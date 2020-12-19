from typing import List, TypeVar, Generic

T = TypeVar('T')


class Node(Generic[T]):
    def __init__(self, concept: T, children: List['Node'] = None):
        if children is None:
            children = []

        self._concept = concept
        self._children = children

    def concept(self) -> T:
        return self._concept

    def children(self) -> List['Node']:
        return self._children

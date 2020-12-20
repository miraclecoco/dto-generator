from typing import TypeVar, Generic, List
from abc import ABC, abstractmethod

from internal.codegen.common.ast import Node as BaseNode
from internal.codegen.php.printer.common import PrinterFactory

T = TypeVar('T')


class Node(BaseNode[T], Generic[T], ABC):
    def __init__(self, children: List['Node'] = None):
        super().__init__(self, children)

    @abstractmethod
    def is_logical(self) -> bool:
        pass

    def is_leaf(self) -> bool:
        return len(self.children()) == 0


class PhysicalComponent(Node[T], Generic[T], ABC):
    def is_logical(self) -> bool:
        return False


class LogicalComponent(Node[T], Generic[T], ABC):
    def is_logical(self) -> bool:
        return True


class Container(ABC):
    pass


class Identifier(PhysicalComponent['Identifier']):
    def __init__(self, represent: str):
        super().__init__()

        self._represent = represent

    def represent(self) -> str:
        return self._represent

    def is_logical(self) -> bool:
        return False


class Type(PhysicalComponent['Type']):
    def __init__(self, represent: str):
        super().__init__()

        self._represent = represent

    @staticmethod
    def string() -> 'Type':
        return Type("string")

    @staticmethod
    def number() -> 'Type':
        return Type("number")

    @staticmethod
    def boolean() -> 'Type':
        return Type("boolean")

    @staticmethod
    def null() -> 'Type':
        return Type("null")

    @staticmethod
    def undefined() -> 'Type':
        return Type("undefined")

    @staticmethod
    def callable() -> 'Type':
        return Type("callable")

    @staticmethod
    def any() -> 'Type':
        return Type("mixed")

    @staticmethod
    def array() -> 'Type':
        return Type("array")

    @staticmethod
    def dictionary() -> 'Type':
        return Type("array")

    @staticmethod
    def instance(name: str) -> 'Type':
        return Type(name)

    def represent(self) -> str:
        return self._represent

    def is_logical(self) -> bool:
        return False


class Statement(PhysicalComponent[T], PrinterFactory, Generic[T], ABC):
    pass


class StatementBlock(Statement[T], Generic[T], ABC):
    pass


class Expression(PhysicalComponent[T], PrinterFactory, Generic[T], ABC):
    @abstractmethod
    def type(self) -> Type:
        pass


class LeftValue(Expression[T], Generic[T], ABC):
    pass


class RightValue(Expression[T], Generic[T], ABC):
    pass


class Reference(LeftValue[T], RightValue[T], Generic[T], ABC):
    pass


class Evaluation(RightValue[T], Generic[T], ABC):
    pass


class Callable(Evaluation[T], Generic[T], ABC):
    def type(self) -> Type:
        return Type.callable()

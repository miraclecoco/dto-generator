from abc import ABC
from typing import Generic, TypeVar, List

from internal.codegen.common.printer import Printer as BasePrinter, PrinterFactory

T = TypeVar('T')


class Printer(BasePrinter, Generic[T], ABC):
    def __init__(self, node: T, parent: BasePrinter = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def node(self) -> T:
        return self._node

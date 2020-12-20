from typing import List, TypeVar, Generic

from internal.codegen.common.util import ListCollection
from internal.codegen.php.ast import StatementBlock
from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext

T = TypeVar('T')


class Collection(Generic[T]):
    def __init__(self, elements: List[T]):
        self._elements = elements

    def elements(self) -> List[T]:
        return self._elements

    def length(self) -> int:
        return len(self.elements())


class StatementBlockCollection(ListCollection[StatementBlock[T]], PrinterFactory, Generic[T]):
    def __init__(self, statement_blocks: List[StatementBlock[T]]):
        super().__init__(statement_blocks)

    def clone(self) -> 'StatementBlockCollection[T]':
        return StatementBlockCollection[T](self._elements)

    def create_printer(self, parent: Printer) -> Printer:
        return StatementBlockCollectionPrinter(self, parent, self.elements())


class StatementBlockCollectionPrinter(Printer):
    def __init__(self, node: StatementBlockCollection, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "\n".join(printer.print(context.create_child()) for printer in self.children())

from typing import List, TypeVar, Generic

from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext
from internal.codegen.ts.ast import StatementBlock
from internal.codegen.ts.element import Modifier

T = TypeVar('T')


class Collection(Generic[T]):
    def __init__(self, elements: List[T]):
        self._elements = elements

    def elements(self) -> List[T]:
        return self._elements

    def length(self) -> int:
        return len(self.elements())


class StatementBlockCollection(PrinterFactory, Collection[StatementBlock]):
    def __init__(self, statement_blocks: List[StatementBlock]):
        super().__init__(statement_blocks)

    def create_printer(self, parent: Printer) -> Printer:
        return StatementBlockCollectionPrinter(self, parent, self.elements())


class StatementBlockCollectionPrinter(Printer):
    def __init__(self, node: StatementBlockCollection, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "\n".join(printer.print(context.create_child()) for printer in self.children())


class ModifierList(PrinterFactory, Collection[Modifier]):
    def __init__(self, modifiers: List[Modifier]):
        super().__init__(modifiers)

    def create_printer(self, parent: Printer) -> Printer:
        return ModifierListPrinter(self, parent, self.elements())


class ModifierListPrinter(Printer):
    def __init__(self, node: ModifierList, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return " ".join(printer.print(context.create_child()) for printer in self.children())

from typing import List

from .ast import StatementBlock
from .util import StatementBlockCollection
from .printer import IndentMiddleware
from ..printer import HighOrderPrinter, PrintContext, Printer, PrinterConfig


class SourceFile:
    def __init__(self, statement_blocks: List[StatementBlock]):
        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def print(self) -> str:
        def print_fn(printer: Printer, context: PrintContext) -> str:
            components = [child.print(context.create_child()) for child in printer.children()]
            return "\n".join(components)

        return HighOrderPrinter(print_fn, None, [self._statement_blocks]) \
            .print(PrintContext.initial(PrinterConfig.default(), [IndentMiddleware()]))

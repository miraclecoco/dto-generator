from typing import List

from internal.codegen.common.printer import HighOrderPrinter, PrintContext, Printer, PrinterConfig
from internal.codegen.php.ast import StatementBlock
from internal.codegen.php.util import StatementBlockCollection
from internal.codegen.php.middleware import IndentMiddleware


class SourceFile:
    def __init__(self, statement_blocks: List[StatementBlock]):
        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def print(self) -> str:
        def print_fn(printer: Printer, context: PrintContext) -> str:
            components = [child.print(context.create_child()) for child in printer.children()]
            return "\n".join(components)

        return HighOrderPrinter(print_fn, None, [self._statement_blocks]) \
            .print(PrintContext.initial(PrinterConfig.default(), [IndentMiddleware()]))

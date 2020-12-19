from internal.codegen.common.printer import PrintContext
from internal.codegen.php.ast import Identifier, Type
from internal.codegen.php.printer.common import Printer


class IdentifierPrinter(Printer[Identifier]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().represent()


class TypePrinter(Printer[Type]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().represent()

from internal.codegen.php.util import StatementBlockCollectionPrinter
from internal.codegen.common.printer import PrinterMiddleware, PrintContext


class IndentMiddleware(PrinterMiddleware):
    def transform(self, context: PrintContext, content: str) -> str:
        if not isinstance(context.stack()[0], StatementBlockCollectionPrinter):
            return content

        n = context.state().indent_size()
        prefix = context.config().indent().process(n)

        return "\n".join(prefix + line for line in content.splitlines())

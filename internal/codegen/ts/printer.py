from .util import StatementBlockCollectionPrinter
from ..printer import PrinterMiddleware, PrintContext


class IndentMiddleware(PrinterMiddleware):
    def transform(self, context: PrintContext, content: str) -> str:
        print(context.stack())
        if not isinstance(context.stack()[0], StatementBlockCollectionPrinter):
            return content

        n = context.state().indent_size()
        prefix = context.config().indent().process(n)

        return "\n".join(prefix + line for line in content.splitlines())

from typing import List

from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext
from internal.codegen.php.grammer import SingleLineComment, MultiLineComment, Class, Member, Method, UnaryOperator, \
    UnaryEvaluation, UnaryAssignment, AnyEvaluation, Accessor


class SingleLineCommentPrinter(Printer):
    def __init__(self, node: SingleLineComment, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "// {0}".format(self._node.content())


class MultiLineCommentPrinter(Printer):
    def __init__(self, node: MultiLineComment, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        s = ""
        s += "/**\n"
        s += "".join([" * {0}\n".format(line) for line in self._node.lines()])
        s += " */"
        return s


class ClassPrinter(Printer):
    def __init__(self, node: Class, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        def configure(ctx: PrintContext):
            ctx.state().set_indent_size(1)

        return "class {0} {{\n{1}\n}}".format(*[
            printer.print(context.create_child(configure)) for printer in self.children()
        ])


class MemberPrinter(Printer):
    def __init__(self, node: Member, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} ${1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class MethodPrinter(Printer):
    def __init__(self, node: Method, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} function {1}({2}) {{\n{4}\n}}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryOperatorPrinter(Printer):
    def __init__(self, node: UnaryOperator, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()


class UnaryEvaluationPrinter(Printer):
    def __init__(self, node: UnaryEvaluation, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} {1} {2}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryAssignmentPrinter(Printer):
    def __init__(self, node: UnaryAssignment, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} = {1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class AnyEvaluationPrinter(Printer):
    def __init__(self, node: AnyEvaluation, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.expression()


class AccessorPrinter(Printer):
    def __init__(self, node: Accessor, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()

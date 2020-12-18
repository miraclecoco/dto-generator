from typing import List, Generic, TypeVar

from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext
from internal.codegen.ts.grammer import SingleLineComment, MultiLineComment, Class, Member, Method, UnaryOperator, \
    UnaryEvaluation, UnaryAssignment, AnyEvaluation, Accessor

T = TypeVar('T')


class NodePrinter(Generic[T], Printer):
    def __init__(self, node: T, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def node(self) -> T:
        return self._node

    def do_print(self, context: PrintContext) -> str:
        raise NotImplementedError()


class SingleLineCommentPrinter(NodePrinter[SingleLineComment]):
    def do_print(self, context: PrintContext) -> str:
        return "// {0}".format(self.node().content())


class MultiLineCommentPrinter(NodePrinter[MultiLineComment]):
    def do_print(self, context: PrintContext) -> str:
        s = ""
        s += "/**\n"
        s += "".join([" * {0}\n".format(line) for line in self.node().lines()])
        s += " */"
        return s


class ClassPrinter(NodePrinter[Class]):
    def do_print(self, context: PrintContext) -> str:
        def configure(ctx: PrintContext):
            ctx.state().set_indent_size(1)

        return "class {0} {{\n{1}\n}}".format(*[
            printer.print(context.create_child(configure)) for printer in self.children()
        ])


class MemberPrinter(NodePrinter[Member]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} {1}: {2};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class MethodPrinter(NodePrinter[Method]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} {1}({2}): {3} {{\n{4}\n}}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryOperatorPrinter(NodePrinter[UnaryOperator]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().represent()


class UnaryEvaluationPrinter(NodePrinter[UnaryEvaluation]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} {1} {2}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryAssignmentPrinter(NodePrinter[UnaryAssignment]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} = {1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class AnyEvaluationPrinter(NodePrinter[AnyEvaluation]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().expression()


class AccessorPrinter(NodePrinter[Accessor]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().represent()

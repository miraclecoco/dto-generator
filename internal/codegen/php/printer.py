from typing import List, TypeVar, Generic

from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext
from internal.codegen.php.ast import Identifier, Type, BlankLine
from internal.codegen.php.element import ArgumentDeclaration, ArgumentDeclarationList, ParameterList, Parameter
from internal.codegen.php.grammer import SingleLineCommentStatement, MultiLineCommentStatement, ClassDeclaration, \
    MemberDeclaration, MethodDeclaration, UnaryOperator, UnaryEvaluation, UnaryAssignmentStatement, AnyEvaluation, \
    AccessStatement, UseStatement, NamespaceDeclaration, Return, InvocationStatement, NamedCallableReference

T = TypeVar('T')


class NodePrinter(Generic[T], Printer):
    def __init__(self, node: T, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def node(self) -> T:
        return self._node

    def do_print(self, context: PrintContext) -> str:
        raise NotImplementedError()


class IdentifierPrinter(NodePrinter[Identifier]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().represent()


class TypePrinter(NodePrinter[Type]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().represent()


class BlankLinePrinter(NodePrinter[BlankLine]):
    def do_print(self, context: PrintContext) -> str:
        return "\n"


class ArgumentDeclarationPrinter(NodePrinter[ArgumentDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        components = [printer.print(context.create_child()) for printer in self.children()]
        return "${0}".format(*components)


class ArgumentDeclarationListPrinter(NodePrinter[ArgumentDeclarationList]):
    def do_print(self, context: PrintContext) -> str:
        components = [printer.print(context.create_child()) for printer in self.children()]
        return ", ".join(components)


class NamespacePrinter(NodePrinter[NamespaceDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        return "namespace {0};".format(self.node().name())


class UsePrinter(NodePrinter[UseStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "use {0};".format(self.node().qualified_name())


class SingleLineCommentPrinter(NodePrinter[SingleLineCommentStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "// {0}".format(self.node().content())


class MultiLineCommentPrinter(NodePrinter[MultiLineCommentStatement]):
    def do_print(self, context: PrintContext) -> str:
        s = ""
        s += "/**\n"
        s += "".join([" * {0}\n".format(line) for line in self.node().lines()])
        s += " */"
        return s


class ClassPrinter(NodePrinter[ClassDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        def configure(ctx: PrintContext):
            ctx.state().set_indent_size(1)

        return "class {0} {{\n{1}\n}}".format(self.node().identifier().represent(), *[
            printer.print(context.create_child(configure)) for printer in self.children()
        ])


class MemberPrinter(NodePrinter[MemberDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} ${1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class MethodPrinter(NodePrinter[MethodDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} function {1}({2}) {{\n{3}\n}}".format(*[
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


class UnaryAssignmentPrinter(NodePrinter[UnaryAssignmentStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} = {1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class AnyEvaluationPrinter(NodePrinter[AnyEvaluation]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().expression()


class AccessStatementPrinter(NodePrinter[AccessStatement]):
    def do_print(self, context: PrintContext) -> str:
        current = self.node()
        accessors = []

        while current is not None:
            accessors.append(current)
            current = current.parent()

        return '->'.join([accessor.name() for accessor in accessors[::-1]])


class ReturnPrinter(NodePrinter[Return]):
    def do_print(self, context: PrintContext) -> str:
        eval_printer = self.children()[0]

        return "return {0};".format(eval_printer.print(context.create_child()))


class NamedCallableReferencePrinter(NodePrinter[NamedCallableReference]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().name()


class ParameterPrinter(NodePrinter[Parameter]):
    def do_print(self, context: PrintContext) -> str:
        evaluation_printer = self.children()[0]
        return evaluation_printer.print(context.create_child())


class ParameterListPrinter(NodePrinter[ParameterList]):
    def do_print(self, context: PrintContext) -> str:
        parameter_printers = self.children()
        return ", ".join([printer.print(context.create_child()) for printer in parameter_printers])


class InvocationPrinter(NodePrinter[InvocationStatement]):
    def do_print(self, context: PrintContext) -> str:
        fn_printer, type_printer, parameter_list_printer = self.children()

        return "{0}({1})".format(
            fn_printer.print(context.create_child()), parameter_list_printer.print(context.create_child())
        )

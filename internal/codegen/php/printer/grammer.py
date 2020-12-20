from typing import TypeVar

from internal.codegen.common.printer import PrintContext
from internal.codegen.common.util import ListCollection
from internal.codegen.php.element import ArgumentDeclaration, ArgumentListDeclaration, ParameterList, Parameter
from internal.codegen.php.grammer import SingleLineCommentStatement, MultiLineCommentStatement, ClassDeclaration, \
    MemberDeclaration, MethodDeclaration, UnaryEvaluation, UnaryAssignmentStatement, AnyEvaluation, Accessor, \
    UseStatement, NamespaceDeclaration, ReturnStatement, InvocationStatement, NamedCallableReference, \
    BlankLineStatement, MethodBody, ArrayDeclaration, ArrayElementDeclaration
from internal.codegen.php.printer.common import Printer

T = TypeVar('T')


class ArgumentDeclarationPrinter(Printer[ArgumentDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        identifier = self.node().identifier().represent()

        return "${0}".format(identifier)


class ArgumentListDeclarationPrinter(Printer[ArgumentListDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        components = [printer.print(context.create_child()) for printer in self.children()]

        return ", ".join(components)


class NamespacePrinter(Printer[NamespaceDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        return "namespace {0};".format(self.node().name())


class UsePrinter(Printer[UseStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "use {0};".format(self.node().qualified_name())


class SingleLineCommentPrinter(Printer[SingleLineCommentStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "// {0}".format(self.node().content())


class MultiLineCommentPrinter(Printer[MultiLineCommentStatement]):
    def do_print(self, context: PrintContext) -> str:
        s = ""
        s += "/**\n"
        s += "".join([" * {0}\n".format(line) for line in self.node().lines()])
        s += " */"
        return s


class ClassDeclarationPrinter(Printer[ClassDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        def configure(ctx: PrintContext):
            ctx.state().set_indent_size(1)

        return "class {0} {{\n{1}\n}}".format(self.node().identifier().represent(), *[
            printer.print(context.create_child(configure)) for printer in self.children()
        ])


class MemberDeclarationPrinter(Printer[MemberDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        access_modifier = self.node().access_modifier().represent()
        static_modifier = " static" if self.node().is_static() else ""
        identifier = self.node().identifier().represent()

        return "{0}{1} ${2};".format(
            access_modifier, static_modifier, identifier
        )


class MethodBodyPrinter(Printer[MethodBody]):
    def do_print(self, context: PrintContext) -> str:
        block_printer = self.children()[0]

        return block_printer.print(context.create_child())


class MethodPrinter(Printer[MethodDeclaration]):
    def do_print(self, context: PrintContext) -> str:
        access_modifier = self.node().access_modifier().represent()
        static_modifier = " static" if self.node().is_static() else ""
        identifier = self.node().identifier().represent()
        argument_list = self.children()[0].print(context.create_child())
        body = self.children()[1].print(context.create_child())

        return "{0}{1} function {2}({3}) {{\n{4}\n}}".format(
            access_modifier, static_modifier, identifier, argument_list, body
        )


class UnaryEvaluationPrinter(Printer[UnaryEvaluation]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} {1} {2}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryAssignmentPrinter(Printer[UnaryAssignmentStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "{0} = {1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class AnyEvaluationPrinter(Printer[AnyEvaluation]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().expression()


class AccessorPrinter(Printer[Accessor]):
    def do_print(self, context: PrintContext) -> str:
        current = self.node()
        accessors = []

        while current is not None:
            accessors.append(current)
            current = current.parent()

        return '->'.join([accessor.name() for accessor in accessors[::-1]])


class ReturnPrinter(Printer[ReturnStatement]):
    def do_print(self, context: PrintContext) -> str:
        eval_printer = self.children()[0]

        return "return {0};".format(eval_printer.print(context.create_child()))


class NamedCallableReferencePrinter(Printer[NamedCallableReference]):
    def do_print(self, context: PrintContext) -> str:
        return self.node().name()


class ParameterPrinter(Printer[Parameter]):
    def do_print(self, context: PrintContext) -> str:
        evaluation_printer = self.children()[0]

        return evaluation_printer.print(context.create_child())


class ParameterListPrinter(Printer[ParameterList]):
    def do_print(self, context: PrintContext) -> str:
        parameter_printers = self.children()
        return ", ".join([printer.print(context.create_child()) for printer in parameter_printers])


class InvocationPrinter(Printer[InvocationStatement]):
    def do_print(self, context: PrintContext) -> str:
        fn_printer, parameter_list_printer = self.children()

        return "{0}({1})".format(
            fn_printer.print(context.create_child()), parameter_list_printer.print(context.create_child())
        )


class ArrayElementDeclarationPrinter(Printer[ArrayElementDeclaration]):
    def do_print(self, context: 'PrintContext') -> str:
        parent_printer = self.parent()  # type: Printer[ArrayDeclaration]
        value_printer = self.children()[0]

        if parent_printer.node().is_dictionary():
            return '"{0}" => {1}'.format(self.node().key(), value_printer.print(context.create_child()))
        else:
            return "{0}".format(value_printer.print(context.create_child()))


class ArrayDeclarationPrinter(Printer[ArrayDeclaration]):
    def do_print(self, context: 'PrintContext') -> str:
        element_printers = self.children()
        exprs = [printer.print(context.create_child()) for printer in element_printers]

        needs_wrap = ListCollection(exprs).reduce(0, lambda n, elem: n + len(elem)) > 80
        indent = context.config().indent().process(1)

        if needs_wrap:
            return "array(\n{0}{1}\n)".format(indent, ",\n{0}".format(indent).join(exprs))
        else:
            return "array({0})".format(", ".join(exprs))


class BlankLinePrinter(Printer[BlankLineStatement]):
    def do_print(self, context: PrintContext) -> str:
        return "\n"

from typing import List

from .ast import Identifier, Type, StatementBlock, LeftValue, RightValue, Evaluation, Reference
from .element import VariableDeclaration, FunctionDeclaration, Modifier
from internal.codegen.printer import Printer, PrinterFactory, PrintContext
from .util import StatementBlockCollection, ModifierList


class Comment(StatementBlock):
    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class SingleLineComment(Comment):
    def __init__(self, content: str):
        self._content = content

    def content(self) -> str:
        return self._content

    def create_printer(self, parent: Printer) -> Printer:
        return SingleLineCommentPrinter(self, parent)


class SingleLineCommentPrinter(Printer):
    def __init__(self, node: SingleLineComment, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "// {0}".format(self._node.content())


class MultiLineComment(Comment):
    def __init__(self, lines: List[str]):
        self._content = lines

    def lines(self) -> List[str]:
        return self._content

    def create_printer(self, parent: Printer) -> Printer:
        return MultiLineCommentPrinter(self, parent)


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


class Class(StatementBlock):
    def __init__(self, name: str, statement_blocks: List[StatementBlock]):
        self._identifier = Identifier(name)
        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return Type(self.identifier().represent())

    def create_printer(self, parent: Printer) -> Printer:
        return ClassPrinter(self, parent, [self.identifier(), self._statement_blocks])


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


class Member(StatementBlock):
    def __init__(self, modifiers: List[Modifier], declaration: VariableDeclaration):
        self._modifiers = ModifierList(modifiers)
        self._declaration = declaration

    def create_printer(self, parent: Printer) -> Printer:
        return MemberPrinter(self, parent, [
            self._modifiers, self._declaration.identifier(), self._declaration.type()
        ])


class MemberPrinter(Printer):
    def __init__(self, node: Member, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} {1}: {2};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class Method(StatementBlock):
    def __init__(self, modifiers: List[Modifier], declaration: FunctionDeclaration,
                 statement_blocks: List[StatementBlock]):
        self._modifiers = ModifierList(modifiers)
        self._declaration = declaration
        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def create_printer(self, parent: Printer) -> Printer:
        decl = self._declaration

        return MethodPrinter(self, parent, [
            self._modifiers, decl.identifier(), decl.argument_list(), decl.return_type(), self._statement_blocks
        ])


class MethodPrinter(Printer):
    def __init__(self, node: Method, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} {1}({2}): {3} {{\n{4}\n}}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryOperator(PrinterFactory):
    def __init__(self, represent: str, typ: Type):
        self._represent = represent
        self._type = typ

    @staticmethod
    def triple_equal():
        return UnaryOperator("===", Type.boolean())

    @staticmethod
    def double_equal():
        return UnaryOperator("==", Type.boolean())

    @staticmethod
    def great_than():
        return UnaryOperator(">", Type.boolean())

    @staticmethod
    def great_than_or_equal():
        return UnaryOperator(">=", Type.boolean())

    @staticmethod
    def less_than():
        return UnaryOperator("<", Type.boolean())

    @staticmethod
    def less_than_or_equal():
        return UnaryOperator("<=", Type.boolean())

    @staticmethod
    def not_triple_equal():
        return UnaryOperator("!==", Type.boolean())

    @staticmethod
    def not_double_equal():
        return UnaryOperator("!=", Type.boolean())

    @staticmethod
    def instanceof():
        return UnaryOperator("instanceof", Type.boolean())

    def represent(self) -> str:
        return self._represent

    def type(self) -> Type:
        return self._type

    def create_printer(self, parent: Printer) -> Printer:
        return UnaryOperatorPrinter(self, parent)


class UnaryOperatorPrinter(Printer):
    def __init__(self, node: UnaryOperator, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()


class UnaryEvaluation(Evaluation):
    def __init__(self, operator: UnaryOperator, left: Evaluation, right: Evaluation):
        self._operator = operator
        self._left = left
        self._right = right

    def operator(self) -> UnaryOperator:
        return self._operator

    def left(self) -> Evaluation:
        return self._left

    def right(self) -> Evaluation:
        return self._right

    def type(self) -> Type:
        return self.operator().type()

    def create_printer(self, parent: Printer) -> Printer:
        return UnaryEvaluationPrinter(self, parent, [
            self.left(), self.operator(), self.right()
        ])


class UnaryEvaluationPrinter(Printer):
    def __init__(self, node: UnaryEvaluation, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} {1} {2}".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class UnaryAssignment(StatementBlock):
    def __init__(self, left: LeftValue, right: RightValue):
        self._left = left
        self._right = right

    def left(self) -> LeftValue:
        return self._left

    def right(self) -> RightValue:
        return self._right

    def type(self) -> Type:
        return self.right().type()

    def create_printer(self, parent: Printer) -> Printer:
        return UnaryAssignmentPrinter(self, parent, [
            self.left(), self.right()
        ])


class UnaryAssignmentPrinter(Printer):
    def __init__(self, node: UnaryAssignment, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return "{0} = {1};".format(*[
            printer.print(context.create_child()) for printer in self.children()
        ])


class AnyEvaluation(Evaluation):
    def __init__(self, expression: str, typ: Type):
        self._expression = expression
        self._type = typ

    def expression(self) -> str:
        return self._expression

    def type(self) -> Type:
        return self._type

    def create_printer(self, parent: Printer) -> Printer:
        return AnyEvaluationPrinter(self, parent)


class AnyEvaluationPrinter(Printer):
    def __init__(self, node: AnyEvaluation, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.expression()


class Accessor(Reference):
    def __init__(self, name: str, typ: Type, parent: 'Accessor' = None):
        self._name = name
        self._type = typ
        self._parent = parent

    @staticmethod
    def series(accessors: List['Accessor']) -> 'Accessor':
        if len(accessors) == 0:
            raise ValueError("'accessors' could not be empty")

        tail = accessors[::-1]

        # get the last accessor
        accessor = tail[0]

        while len(tail) > 1:
            head = tail[0]
            head.set_parent(tail[1])
            tail = tail[1:]

        return accessor

    def name(self) -> str:
        return self._name

    def type(self) -> Type:
        return self._type

    def parent(self) -> 'Accessor':
        return self._parent

    def represent(self) -> str:
        current = self
        accessors = []

        while current is not None:
            accessors.append(current)
            current = current.parent()

        return '.'.join([accessor.name() for accessor in accessors[::-1]])

    def set_parent(self, parent: 'Accessor') -> None:
        self._parent = parent

    def create_printer(self, parent: Printer) -> Printer:
        return AccessorPrinter(self, parent)


class AccessorPrinter(Printer):
    def __init__(self, node: Accessor, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()


class Scope:
    def __init__(self, typ: Type):
        self._type = typ

    def type(self) -> Type:
        return self._type


class ThisAccessor(Accessor):
    def __init__(self, scope: Scope):
        super().__init__("this", scope.type())

        self._scope = scope

    def scope(self) -> Scope:
        return self._scope

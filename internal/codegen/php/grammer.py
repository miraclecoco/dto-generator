from typing import List

from internal.codegen.common.printer import Printer, PrinterFactory
from internal.codegen.php.ast import Identifier, Type, StatementBlock, LeftValue, RightValue, Evaluation, Reference, \
    CallableReference
from internal.codegen.php.element import VariableDeclaration, FunctionDeclaration, Modifier, ParameterList
from internal.codegen.php.util import StatementBlockCollection, ModifierList


class NamespaceDeclaration(StatementBlock):
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import NamespacePrinter

        return NamespacePrinter(self, parent)


class UseStatement(StatementBlock):
    def __init__(self, qualified_name: str):
        self._qualified_name = qualified_name

    def qualified_name(self) -> str:
        return self._qualified_name

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import UsePrinter

        return UsePrinter(self, parent)


class CommentStatement(StatementBlock):
    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class SingleLineCommentStatement(CommentStatement):
    def __init__(self, content: str):
        self._content = content

    def content(self) -> str:
        return self._content

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import SingleLineCommentPrinter

        return SingleLineCommentPrinter(self, parent)


class MultiLineCommentStatement(CommentStatement):
    def __init__(self, lines: List[str]):
        self._content = lines

    def lines(self) -> List[str]:
        return self._content

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import MultiLineCommentPrinter

        return MultiLineCommentPrinter(self, parent)


class ClassDeclaration(StatementBlock):
    def __init__(self, name: str, statement_blocks: List[StatementBlock]):
        self._identifier = Identifier(name)
        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return Type(self.identifier().represent())

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import ClassPrinter

        return ClassPrinter(self, parent, [self._statement_blocks])


class MemberDeclaration(StatementBlock):
    def __init__(self, modifiers: List[Modifier], variable: VariableDeclaration):
        self._modifiers = ModifierList(modifiers)
        self._variable = variable

    def modifiers(self) -> ModifierList:
        return self._modifiers

    def variable(self) -> VariableDeclaration:
        return self._variable

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import MemberPrinter

        return MemberPrinter(self, parent, [
            self.modifiers(), self.variable().identifier()
        ])


class MethodDeclaration(StatementBlock):
    def __init__(self, modifiers: List[Modifier], function: FunctionDeclaration,
                 statement_blocks: List[StatementBlock]):
        self._modifiers = ModifierList(modifiers)
        self._function = function
        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def modifiers(self) -> ModifierList:
        return self._modifiers

    def function(self) -> FunctionDeclaration:
        return self._function

    def statement_blocks(self) -> StatementBlockCollection:
        return self._statement_blocks

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import MethodPrinter

        decl = self.function()

        return MethodPrinter(self, parent, [
            self.modifiers(), decl.identifier(), decl.argument_list(), self.statement_blocks()
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
        from internal.codegen.php.printer import UnaryOperatorPrinter

        return UnaryOperatorPrinter(self, parent)


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
        from internal.codegen.php.printer import UnaryEvaluationPrinter

        return UnaryEvaluationPrinter(self, parent, [
            self.left(), self.operator(), self.right()
        ])


class UnaryAssignmentStatement(StatementBlock):
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
        from internal.codegen.php.printer import UnaryAssignmentPrinter

        return UnaryAssignmentPrinter(self, parent, [
            self.left(), self.right()
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
        from internal.codegen.php.printer import AnyEvaluationPrinter

        return AnyEvaluationPrinter(self, parent)


class AccessStatement(Reference):
    def __init__(self, name: str, typ: Type, parent: 'AccessStatement' = None):
        self._name = name
        self._type = typ
        self._parent = parent

    @staticmethod
    def series(accessors: List['AccessStatement']) -> 'AccessStatement':
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

    def parent(self) -> 'AccessStatement':
        return self._parent

    def set_parent(self, parent: 'AccessStatement') -> None:
        self._parent = parent

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import AccessStatementPrinter

        return AccessStatementPrinter(self, parent)


class Scope:
    def __init__(self, typ: Type):
        self._type = typ

    def type(self) -> Type:
        return self._type


class AccessThisStatement(AccessStatement):
    def __init__(self, scope: Scope):
        super().__init__("$this", scope.type())

        self._scope = scope

    def scope(self) -> Scope:
        return self._scope


class Return(StatementBlock):
    def __init__(self, evaluation: Evaluation):
        self._evaluation = evaluation

    def evaluation(self) -> Evaluation:
        return self._evaluation

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import ReturnPrinter

        return ReturnPrinter(self, parent, [self.evaluation()])


class NamedCallableReference(CallableReference):
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import NamedCallableReferencePrinter

        return NamedCallableReferencePrinter(self, parent)


class InvocationStatement(Evaluation):
    def __init__(self, call: CallableReference, typ: Type, parameters: ParameterList):
        self._callable = call
        self._type = typ
        self._parameters = parameters

    def callable(self) -> CallableReference:
        return self._callable

    def type(self) -> Type:
        return self._type

    def parameters(self) -> ParameterList:
        return self._parameters

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import InvocationPrinter

        return InvocationPrinter(self, parent, [self.callable(), self.type(), self.parameters()])

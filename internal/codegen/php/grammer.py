from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic

from internal.codegen.common.printer import PassThroughPrinter
from internal.codegen.php.convension import AccessModifier, UnaryOperator
from internal.codegen.php.printer.common import BasePrinter, Printer, PrinterFactory
from internal.codegen.php.ast import Identifier, Type, StatementBlock, LeftValue, RightValue, Evaluation, Reference, \
    Callable, Node, LogicalComponent
from internal.codegen.php.element import ParameterList, ArgumentListDeclaration
from internal.codegen.php.util import StatementBlockCollection

T = TypeVar('T')


class NamespaceDeclaration(StatementBlock['NamespaceDeclaration']):
    def __init__(self, name: str):
        super().__init__()

        self._name = name

    def name(self) -> str:
        return self._name

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import NamespacePrinter

        return NamespacePrinter(self, parent)


class UseStatement(StatementBlock['UseStatement']):
    def __init__(self, qualified_name: str):
        super().__init__()

        self._qualified_name = qualified_name

    def qualified_name(self) -> str:
        return self._qualified_name

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import UsePrinter

        return UsePrinter(self, parent)


class SingleLineCommentStatement(StatementBlock['SingleLineCommentStatement']):
    def __init__(self, content: str):
        super().__init__()

        self._content = content

    def content(self) -> str:
        return self._content

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import SingleLineCommentPrinter

        return SingleLineCommentPrinter(self, parent)


class MultiLineCommentStatement(StatementBlock['MultiLineCommentStatement']):
    def __init__(self, lines: List[str]):
        super().__init__()

        self._content = lines

    def lines(self) -> List[str]:
        return self._content

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import MultiLineCommentPrinter

        return MultiLineCommentPrinter(self, parent)


class ClassDeclaration(StatementBlock['ClassDeclaration']):
    def __init__(self, identifier: Identifier, fields: List['StatementBlock']):
        super().__init__(fields)

        self._identifier = identifier
        self._fields = StatementBlockCollection(fields)

    def identifier(self) -> Identifier:
        return self._identifier

    def fields(self) -> StatementBlockCollection:
        return self._fields

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import ClassDeclarationPrinter

        return ClassDeclarationPrinter(self, parent, [self.fields()])


class ClassField(StatementBlock[T], Generic[T], ABC):
    @abstractmethod
    def access_modifier(self) -> AccessModifier:
        pass

    @abstractmethod
    def is_static(self) -> bool:
        pass

    def is_public(self) -> bool:
        return self.access_modifier().is_public()

    def is_protected(self) -> bool:
        return self.access_modifier().is_protected()

    def is_private(self) -> bool:
        return self.access_modifier().is_private()


class MemberDeclaration(ClassField['MethodDeclaration']):
    def __init__(self, identifier: Identifier, typ: Type, access_modifier: AccessModifier, static: bool):
        super().__init__()

        self._identifier = identifier
        self._type = typ
        self._access_modifier = access_modifier
        self._static = static

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._type

    def access_modifier(self) -> AccessModifier:
        return self._access_modifier

    def is_static(self) -> bool:
        return self._static

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import MemberDeclarationPrinter

        return MemberDeclarationPrinter(self, parent)


class MethodBody(LogicalComponent['MethodBody'], PrinterFactory):
    def __init__(self, statement_blocks: List[StatementBlock]):
        super().__init__(statement_blocks)

        self._statement_blocks = StatementBlockCollection(statement_blocks)

    def statement_blocks(self) -> StatementBlockCollection:
        return self._statement_blocks

    def create_printer(self, parent: BasePrinter) -> BasePrinter:
        return PassThroughPrinter(parent, [self.statement_blocks()])


class MethodDeclaration(ClassField['MethodDeclaration']):
    def __init__(self, identifier: Identifier, return_type: Type, access_modifier: AccessModifier, static: bool,
                 argument_list: ArgumentListDeclaration, body: MethodBody):
        super().__init__([body])

        self._identifier = identifier
        self._return_type = return_type
        self._access_modifier = access_modifier
        self._static = static
        self._argument_list = argument_list
        self._body = body

    def identifier(self) -> Identifier:
        return self._identifier

    def return_type(self) -> Type:
        return self._return_type

    def access_modifier(self) -> AccessModifier:
        return self._access_modifier

    def is_static(self) -> bool:
        return self._static

    def argument_list(self) -> ArgumentListDeclaration:
        return self._argument_list

    def body(self) -> MethodBody:
        return self._body

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import MethodPrinter

        return MethodPrinter(self, parent, [self.argument_list(), self.body()])


class UnaryEvaluation(Evaluation['UnaryEvaluation']):
    def __init__(self, operator: UnaryOperator, left: Evaluation, right: Evaluation):
        super().__init__([operator, left, right])

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

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import UnaryEvaluationPrinter

        return UnaryEvaluationPrinter(self, parent, [
            self.left(), self.operator(), self.right()
        ])


class UnaryAssignmentStatement(StatementBlock['UnaryAssignmentStatement']):
    def __init__(self, left: LeftValue, right: RightValue):
        super().__init__([left, right])

        self._left = left
        self._right = right

    def left(self) -> LeftValue:
        return self._left

    def right(self) -> RightValue:
        return self._right

    def type(self) -> Type:
        return self.right().type()

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import UnaryAssignmentPrinter

        return UnaryAssignmentPrinter(self, parent, [
            self.left(), self.right()
        ])


class AnyEvaluation(Evaluation['AnyEvaluation']):
    def __init__(self, expression: str, typ: Type):
        super().__init__()

        self._expression = expression
        self._type = typ

    def expression(self) -> str:
        return self._expression

    def type(self) -> Type:
        return self._type

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import AnyEvaluationPrinter

        return AnyEvaluationPrinter(self, parent)


class Accessor(Reference['Accessor']):
    def __init__(self, name: str, typ: Type, parent: 'Accessor' = None):
        super().__init__()

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

    def set_parent(self, parent: 'Accessor') -> None:
        self._parent = parent

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import AccessorPrinter

        return AccessorPrinter(self, parent)


class Scope:
    def __init__(self, typ: Type):
        self._type = typ

    def type(self) -> Type:
        return self._type


class ThisAccessor(Accessor):
    def __init__(self, scope: Scope):
        super().__init__("$this", scope.type())

        self._scope = scope

    def scope(self) -> Scope:
        return self._scope


class ReturnStatement(StatementBlock['ReturnStatement']):
    def __init__(self, evaluation: Evaluation):
        super().__init__([evaluation])

        self._evaluation = evaluation

    def evaluation(self) -> Evaluation:
        return self._evaluation

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import ReturnPrinter

        return ReturnPrinter(self, parent, [self.evaluation()])


class NamedCallableReference(Callable['NamedCallableReference']):
    def __init__(self, name: str):
        super().__init__()

        self._name = name

    def name(self) -> str:
        return self._name

    def is_logical(self) -> bool:
        return True

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import NamedCallableReferencePrinter

        return NamedCallableReferencePrinter(self, parent)


class InvocationStatement(Evaluation['InvocationStatement']):
    def __init__(self, call: Callable, typ: Type, parameters: ParameterList):
        super().__init__()

        self._callable = call
        self._type = typ
        self._parameters = parameters

    def callable(self) -> Callable:
        return self._callable

    def type(self) -> Type:
        return self._type

    def parameters(self) -> ParameterList:
        return self._parameters

    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import InvocationPrinter

        return InvocationPrinter(self, parent, [self.callable(), self.parameters()])


class BlankLineStatement(StatementBlock['BlankLineStatement']):
    def is_logical(self) -> bool:
        return False

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import BlankLinePrinter

        return BlankLinePrinter(self, parent)

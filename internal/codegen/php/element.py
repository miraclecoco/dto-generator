from typing import List

from internal.codegen.common.printer import PrinterFactory, PassThroughPrinter
from internal.codegen.php.ast import Node, Identifier, Type, Evaluation
from internal.codegen.php.printer.common import BasePrinter, Printer


class VariableDeclaration(Node['VariableDeclaration']):
    def __init__(self, name: str, typ: Type):
        super().__init__()

        self._identifier = Identifier(name)
        self._typ = typ

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._typ

    def is_logical(self) -> bool:
        return True


class ArgumentDeclaration(Node['ArgumentDeclaration'], PrinterFactory):
    def __init__(self, identifier: Identifier, typ: Type):
        super().__init__()

        self._identifier = identifier
        self._type = typ

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._type

    def is_logical(self) -> bool:
        return True

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import ArgumentDeclarationPrinter

        return ArgumentDeclarationPrinter(self, parent)


class ArgumentListDeclaration(Node['ArgumentDeclarationList'], PrinterFactory):
    def __init__(self, arguments: List[ArgumentDeclaration]):
        super().__init__(arguments)

        self._arguments = arguments

    @staticmethod
    def empty():
        return ArgumentListDeclaration([])

    def arguments(self) -> List[ArgumentDeclaration]:
        return self._arguments

    def length(self) -> int:
        return len(self._arguments)

    def is_logical(self) -> bool:
        return True

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import ArgumentListDeclarationPrinter

        return ArgumentListDeclarationPrinter(self, parent, self.arguments())


class FunctionDeclaration(Node['FunctionDeclaration']):
    def __init__(self, identifier: Identifier, return_type: Type, argument_list: ArgumentListDeclaration):
        super().__init__()

        self._identifier = identifier
        self._return_type = return_type
        self._argument_list = argument_list

    def identifier(self) -> Identifier:
        return self._identifier

    def return_type(self) -> Type:
        return self._return_type

    def argument_list(self) -> ArgumentListDeclaration:
        return self._argument_list

    def is_logical(self) -> bool:
        return True


class Parameter(Node['Parameter'], PrinterFactory):
    def __init__(self, index: int, evaluation: Evaluation):
        super().__init__([evaluation])

        self._index = index
        self._evaluation = evaluation

    def index(self) -> int:
        return self._index

    def evaluation(self) -> Evaluation:
        return self._evaluation

    def is_logical(self) -> bool:
        return True

    def create_printer(self, parent: BasePrinter) -> BasePrinter:
        return PassThroughPrinter(parent, [self.evaluation()])


class ParameterList(Node['ParameterList'], PrinterFactory):
    def __init__(self, parameters: List[Evaluation]):
        super().__init__(parameters)

        self._parameters = [Parameter(index, parameters[index]) for index in range(len(parameters))]

    def parameters(self) -> List[Parameter]:
        return self._parameters

    def is_logical(self) -> bool:
        return True

    def create_printer(self, parent: BasePrinter) -> Printer:
        from internal.codegen.php.printer.grammer import ParameterListPrinter

        return ParameterListPrinter(self, parent, self.parameters())

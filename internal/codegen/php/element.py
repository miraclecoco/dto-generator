from typing import List

from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext
from internal.codegen.php.ast import Identifier, Type, Evaluation


class VariableDeclaration:
    def __init__(self, name: str, typ: Type):
        self._identifier = Identifier(name)
        self._typ = typ

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._typ


class ArgumentDeclaration(PrinterFactory):
    def __init__(self, name: str, typ: Type):
        self._identifier = Identifier(name)
        self._type = typ

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._type

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import ArgumentDeclarationPrinter

        return ArgumentDeclarationPrinter(self, parent, [self.identifier()])


class ArgumentDeclarationList(PrinterFactory):
    def __init__(self, arguments: List[ArgumentDeclaration]):
        self._arguments = arguments

    @staticmethod
    def empty():
        return ArgumentDeclarationList([])

    def arguments(self) -> List[ArgumentDeclaration]:
        return self._arguments

    def length(self) -> int:
        return len(self._arguments)

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import ArgumentDeclarationListPrinter

        return ArgumentDeclarationListPrinter(self, parent, self.arguments())


class FunctionDeclaration:
    def __init__(self, name: str, return_type: Type, argument_list: ArgumentDeclarationList):
        self._identifier = Identifier(name)
        self._return_type = return_type
        self._argument_list = argument_list

    def identifier(self) -> Identifier:
        return self._identifier

    def return_type(self) -> Type:
        return self._return_type

    def argument_list(self) -> ArgumentDeclarationList:
        return self._argument_list


class Parameter(PrinterFactory):
    def __init__(self, index: int, evaluation: Evaluation):
        self._index = index
        self._evaluation = evaluation

    def index(self) -> int:
        return self._index

    def evaluation(self) -> Evaluation:
        return self._evaluation

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import ParameterPrinter

        return ParameterPrinter(self, parent, [self.evaluation()])


class ParameterList(PrinterFactory):
    def __init__(self, parameters: List[Evaluation]):
        self._parameters = [Parameter(index, parameters[index]) for index in range(len(parameters))]

    def parameters(self) -> List[Parameter]:
        return self._parameters

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import ParameterListPrinter

        return ParameterListPrinter(self, parent, self.parameters())


class Modifier(PrinterFactory):
    def __init__(self, represent: str):
        self._represent = represent

    def represent(self) -> 'str':
        return self._represent

    def create_printer(self, parent: Printer) -> Printer:
        return ModifierPrinter(self, parent)


class ModifierPrinter(Printer):
    def __init__(self, node: Modifier, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()


class AccessModifier(Modifier):
    @staticmethod
    def public() -> 'AccessModifier':
        return AccessModifier("public")

    @staticmethod
    def protected() -> 'AccessModifier':
        return AccessModifier("protected")

    @staticmethod
    def private() -> 'AccessModifier':
        return AccessModifier("private")


class StaticModifier(Modifier):
    def __init__(self):
        super().__init__("static")

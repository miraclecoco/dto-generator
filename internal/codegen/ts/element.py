from typing import List

from internal.codegen.ts.ast import Identifier, Type
from internal.codegen.common.printer import Printer, PrinterFactory, PrintContext


class VariableDeclaration:
    def __init__(self, name: str, typ: Type):
        self._identifier = Identifier(name)
        self._typ = typ

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._typ


class Argument(PrinterFactory):
    def __init__(self, name: str, typ: Type):
        self._identifier = Identifier(name)
        self._type = typ

    def identifier(self) -> Identifier:
        return self._identifier

    def type(self) -> Type:
        return self._type

    def create_printer(self, parent: Printer) -> Printer:
        return ArgumentPrinter(self, parent, [self.identifier(), self.type()])


class ArgumentPrinter(Printer):
    def __init__(self, node: Argument, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        components = [printer.print(context.create_child()) for printer in self.children()]
        return "{0}: {1}".format(*components)


class ArgumentList(PrinterFactory):
    def __init__(self, arguments: List[Argument]):
        self._arguments = arguments

    @staticmethod
    def empty():
        return ArgumentList([])

    def arguments(self) -> List[Argument]:
        return self._arguments

    def length(self) -> int:
        return len(self._arguments)

    def create_printer(self, parent: Printer) -> Printer:
        return ArgumentListPrinter(self, parent, self.arguments())


class ArgumentListPrinter(Printer):
    def __init__(self, node: ArgumentList, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        components = [printer.print(context.create_child()) for printer in self.children()]
        return ", ".join(components)


class FunctionDeclaration:
    def __init__(self, name: str, return_type: Type, argument_list: ArgumentList):
        self._identifier = Identifier(name)
        self._return_type = return_type
        self._argument_list = argument_list

    def identifier(self) -> Identifier:
        return self._identifier

    def return_type(self) -> Type:
        return self._return_type

    def argument_list(self) -> ArgumentList:
        return self._argument_list


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


class ReadonlyModifier(Modifier):
    def __init__(self):
        super().__init__("readonly")

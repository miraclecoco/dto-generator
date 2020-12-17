from typing import List

from internal.codegen.printer import PrinterFactory, Printer, PrintContext


class Identifier(PrinterFactory):
    def __init__(self, represent: str):
        self._represent = represent

    def represent(self) -> str:
        return self._represent

    def create_printer(self, parent: Printer) -> Printer:
        return IdentifierPrinter(self, parent)


class IdentifierPrinter(Printer):
    def __init__(self, node: Identifier, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()


class Type(PrinterFactory):
    def __init__(self, represent: str):
        self._represent = represent

    @staticmethod
    def string() -> 'Type':
        return Type("string")

    @staticmethod
    def number() -> 'Type':
        return Type("number")

    @staticmethod
    def boolean() -> 'Type':
        return Type("boolean")

    @staticmethod
    def null() -> 'Type':
        return Type("null")

    @staticmethod
    def undefined() -> 'Type':
        return Type("undefined")

    @staticmethod
    def any() -> 'Type':
        return Type("any")

    @staticmethod
    def instance(name: str) -> 'Type':
        return Type(name)

    def represent(self) -> str:
        return self._represent

    def create_printer(self, parent: Printer) -> Printer:
        return TypePrinter(self, parent)


class TypePrinter(Printer):
    def __init__(self, node: Type, parent: Printer = None, children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._node = node

    def do_print(self, context: PrintContext) -> str:
        return self._node.represent()


class Expression(PrinterFactory):
    def type(self) -> Type:
        raise NotImplementedError()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class Statement(PrinterFactory):
    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class StatementBlock(Statement):
    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class LeftValue(PrinterFactory):
    def type(self) -> Type:
        raise NotImplementedError()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class RightValue(Expression):
    def type(self) -> Type:
        raise NotImplementedError()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class Evaluation(RightValue):
    def type(self) -> Type:
        raise NotImplementedError()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class Reference(Evaluation, LeftValue):
    def type(self) -> Type:
        raise NotImplementedError()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()

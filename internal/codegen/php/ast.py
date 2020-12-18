from internal.codegen.common.printer import PrinterFactory, Printer


class Node:
    pass


class Identifier(Node, PrinterFactory):
    def __init__(self, represent: str):
        self._represent = represent

    def represent(self) -> str:
        return self._represent

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import IdentifierPrinter

        return IdentifierPrinter(self, parent)


class Type(Node, PrinterFactory):
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
    def callable() -> 'Type':
        return Type("callable")

    @staticmethod
    def any() -> 'Type':
        return Type("any")

    @staticmethod
    def instance(name: str) -> 'Type':
        return Type(name)

    def represent(self) -> str:
        return self._represent

    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import TypePrinter

        return TypePrinter(self, parent)


class Expression(Node, PrinterFactory):
    def type(self) -> Type:
        raise NotImplementedError()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class Statement(Node, PrinterFactory):
    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class StatementBlock(Statement):
    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()


class BlankLine(StatementBlock):
    def create_printer(self, parent: Printer) -> Printer:
        from internal.codegen.php.printer import BlankLinePrinter

        return BlankLinePrinter(self, parent)


class LeftValue(Node, PrinterFactory):
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


class CallableReference(Evaluation):
    def type(self) -> Type:
        return Type.callable()

    def create_printer(self, parent: Printer) -> Printer:
        raise NotImplementedError()

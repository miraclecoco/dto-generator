from typing import List, Optional

from internal.codegen.common.printer import PrintContext
from internal.codegen.php.printer.common import BasePrinter, Printer
from internal.codegen.php.grammer import MultiLineCommentStatement


class DocCommentStatement(MultiLineCommentStatement):
    def __init__(self, description: Optional[str] = None, annotations: Optional[List['Annotation']] = None):
        super().__init__([])

        self._description = description
        self._annotations = annotations

    def description(self) -> str:
        return self._description

    def annotations(self) -> List['Annotation']:
        return self._annotations

    def should_print_description(self):
        return self.description() is not None

    def should_print_annotation(self):
        return self.annotations() is not None

    def lines(self) -> List[str]:
        return [
            self.description(),
            *["@{0} {1}".format(annotation.name(), annotation.value()) for annotation in self.annotations()]
        ]

    def create_printer(self, parent: BasePrinter) -> Printer:
        return DocCommentStatementPrinter(self, parent)


class DocCommentStatementPrinter(Printer[DocCommentStatement]):
    def do_print(self, context: PrintContext) -> str:
        lines = [
            "/**"
        ]

        if self.node().should_print_description():
            lines.append(" * {0}".format(self.node().description()))

            if self.node().should_print_annotation():
                lines.append(" *")

        if self.node().should_print_annotation():
            for annotation in self.node().annotations():
                lines.append(" * @{0} {1}".format(annotation.name(), annotation.value()))

        lines.append(" */")

        return "\n".join(lines)


class Annotation:
    def __init__(self, name: str, value: str):
        self._name = name
        self._value = value

    @staticmethod
    def param(name: str, typ: str, description: str = None) -> 'Annotation':
        if description is None:
            return Annotation("param", "{0} ${1}".format(typ, name))

        return Annotation("param", "{0} ${1} {2}".format(typ, name, description))

    @staticmethod
    def types(typ: str) -> 'Annotation':
        return Annotation("var", "{0}".format(typ))

    @staticmethod
    def returns(typ: str, description: str = None) -> 'Annotation':
        if description is None:
            return Annotation("return", "{0}".format(typ))
        else:
            return Annotation("return", "{0} {1}".format(typ, description))

    def name(self) -> str:
        return self._name

    def value(self) -> str:
        return self._value

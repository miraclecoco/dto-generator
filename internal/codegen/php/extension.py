from typing import List

from internal.codegen.php.grammer import MultiLineComment


class DocComment(MultiLineComment):
    def __init__(self, description: str, annotations: List['Annotation']):
        super().__init__([])

        self._description = description
        self._annotations = annotations

    def description(self) -> str:
        return self._description

    def annotations(self) -> List['Annotation']:
        return self._annotations

    def lines(self) -> List[str]:
        return [
            self.description(),
            *["@{0} {1}".format(annotation.name(), annotation.value()) for annotation in self.annotations()]
        ]


class Annotation:
    def __init__(self, name: str, value: str):
        self._name = name
        self._value = value

    @staticmethod
    def param(name: str, typ: str, description: str = None) -> 'Annotation':
        if description is None:
            return Annotation("param", "{0} {1}".format(typ, name))

        return Annotation("param", "{0} {1} {2}".format(typ, name, description))

    @staticmethod
    def var(typ: str, description: str = None) -> 'Annotation':
        return Annotation("var", "{0} {1}".format(typ, description))

    def name(self) -> str:
        return self._name

    def value(self) -> str:
        return self._value

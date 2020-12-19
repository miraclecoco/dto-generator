from typing import List, Optional


class Comment:
    def __init__(self, desc: str = None, annotations: List['Annotation'] = None) -> None:
        self._decs = desc
        self._annotations = annotations

    def desc(self) -> Optional[str]:
        return self._decs

    def annotations(self) -> Optional[List['Annotation']]:
        return self._annotations

    def needs_generate(self) -> bool:
        return not not self.desc() or not not self.annotations()


class Annotation:
    def name(self) -> str:
        raise NotImplemented()

    def value(self) -> str:
        raise NotImplemented()


class ParamAnnotation(Annotation):
    def __init__(self, var: str, desc: str = None) -> None:
        self._var = var
        self._desc = desc

    def name(self) -> str:
        return "param"

    def value(self) -> str:
        s = ""
        s += "{0}".format(self._var)

        if self._desc is not None:
            s += " {0}".format(self._desc)

        return s


class CustomAnnotation(Annotation):
    def __init__(self, name: str, value: str) -> None:
        self._name = name
        self._value = value

    def name(self) -> str:
        return self._name

    def value(self) -> str:
        return self._value

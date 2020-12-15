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

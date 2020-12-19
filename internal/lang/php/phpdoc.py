class Annotation:
    def name(self) -> str:
        raise NotImplemented()

    def value(self) -> str:
        raise NotImplemented()


class VarAnnotation(Annotation):
    def __init__(self, typ: str, var: str = None, desc: str = None) -> None:
        self._typ = typ
        self._var = var
        self._desc = desc

    def name(self) -> str:
        return "var"

    def value(self) -> str:
        s = ""
        s += self._typ

        if self._var is not None:
            s += " ${0}".format(self._var)

        if self._desc is not None:
            s += " " + self._desc

        return s


class ParamAnnotation(Annotation):
    def __init__(self, typ: str, var: str, desc: str = None) -> None:
        self._typ = typ
        self._var = var
        self._desc = desc

    def name(self) -> str:
        return "param"

    def value(self) -> str:
        s = ""
        s += "{0} ${1}".format(self._typ, self._var)

        if self._desc is not None:
            s += " " + self._desc

        return s


class ReturnAnnotation(Annotation):
    def __init__(self, typ: str) -> None:
        self._typ = typ

    def name(self) -> str:
        return "return"

    def value(self) -> str:
        return self._typ


class CustomAnnotation(Annotation):
    def __init__(self, name: str, value: str) -> None:
        self._name = name
        self._value = value

    def name(self) -> str:
        return self._name

    def value(self) -> str:
        return self._value

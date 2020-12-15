from typing import IO

from internal.spec import Spec


class Generator:
    @staticmethod
    def get_extension() -> str:
        raise NotImplementedError()

    @staticmethod
    def get_clazz(spec: Spec) -> str:
        raise NotImplementedError()

    def generate(self, spec: Spec, fp: IO) -> None:
        raise NotImplementedError()

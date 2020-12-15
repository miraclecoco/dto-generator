from internal.spec import Spec


class Generator:
    def generate(self, spec: Spec) -> str:
        raise NotImplementedError()
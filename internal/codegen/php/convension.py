from internal.codegen.php.ast import Type


class AccessModifier:
    def __init__(self, represent: str, public: bool, protected: bool, private: bool):
        self._represent = represent
        self._public = public
        self._protected = protected
        self._private = private

    def represent(self) -> str:
        return self._represent

    def is_public(self) -> bool:
        return self._public

    def is_protected(self) -> bool:
        return self._protected

    def is_private(self) -> bool:
        return self._private

    @staticmethod
    def public() -> 'AccessModifier':
        return AccessModifier("public", True, False, False)

    @staticmethod
    def protected() -> 'AccessModifier':
        return AccessModifier("protected", False, True, False)

    @staticmethod
    def private() -> 'AccessModifier':
        return AccessModifier("private", False, False, True)


class UnaryOperator:
    def __init__(self, typ: Type, represent: str):
        self._represent = represent
        self._type = typ

    @staticmethod
    def triple_equal():
        return UnaryOperator(Type.boolean(), "===")

    @staticmethod
    def double_equal():
        return UnaryOperator(Type.boolean(), "==")

    @staticmethod
    def great_than():
        return UnaryOperator(Type.boolean(), ">")

    @staticmethod
    def great_than_or_equal():
        return UnaryOperator(Type.boolean(), ">=")

    @staticmethod
    def less_than():
        return UnaryOperator(Type.boolean(), "<")

    @staticmethod
    def less_than_or_equal():
        return UnaryOperator(Type.boolean(), "<=")

    @staticmethod
    def not_triple_equal():
        return UnaryOperator(Type.boolean(), "!==")

    @staticmethod
    def not_double_equal():
        return UnaryOperator(Type.boolean(), "!=")

    @staticmethod
    def instanceof():
        return UnaryOperator(Type.boolean(), "instanceof")

    def type(self) -> Type:
        return self._type

    def represent(self) -> str:
        return self._represent

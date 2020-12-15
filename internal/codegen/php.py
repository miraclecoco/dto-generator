from typing import List, Optional, IO
from colorama import Fore

from internal.spec import Field, Spec, aggregate_groups_from_fields
from internal.codegen import Generator
from internal.util import upper_first
from internal.lang.php import Comment, VarAnnotation, ReturnAnnotation, ParamAnnotation


def code(s: str) -> str:
    return s.strip()


TEMPLATE = code("""
<?php

// THIS FILE IS AUTO GENERATED

namespace {namespace};

class {clazz} {{
{members}

{constructor}

{deserializers}

{serializers}
}}
""") + "\n"

PHP_TYPE = {
    "string": "string",
    "integer": "int",
    "float": "float",
    "double": "double",
    "boolean": "bool",
    "any": "mixed",
}

PHP_CONVERT_FN = {
    "string": "strval({expr})",
    "integer": "intval({expr})",
    "float": "floatval({expr})",
    "double": "doubleval({expr})",
    "boolean": "boolval({expr})",
}


def get_php_type(typ: str) -> str:
    return PHP_TYPE[typ] if typ in PHP_TYPE else typ


def get_php_convert_func(typ: str) -> Optional[str]:
    return PHP_CONVERT_FN[typ] if typ in PHP_CONVERT_FN else None


def generate_comment(comment: Comment) -> str:
    if not comment.needs_generate():
        return ""

    lines = []

    if comment.desc() is not None:
        lines.append("{0}".format(comment.desc()))

    if comment.annotations() is not None:
        if comment.desc() is not None:
            lines.append("")

        for annotation in comment.annotations():
            lines.append("@{0} {1}".format(annotation.name(), annotation.value()))

    s = ""
    s += "/**\n"
    s += " * " + "\n * ".join(lines) + "\n"
    s += " */"

    return s


def generate_member(field: Field) -> str:
    s = ""
    s += generate_comment(Comment(field.comment(), [
        VarAnnotation(get_php_type(field.type()))
    ]))
    s += "\n"
    s += "public ${0};".format(field.name())

    return s


def generate_members(fields: List[Field]) -> str:
    members = []

    for field in fields:
        members.append(generate_member(field))

    return "\n\n".join(members)


def generate_constructor(fields: List[Field]) -> str:
    arguments = []
    assignments = []

    for field in fields:
        arguments.append("${0}".format(field.name()))
        assignments.append("$this->{0} = ${0};".format(field.name()))

    s = ""
    s += generate_comment(Comment(None, [
        ParamAnnotation(get_php_type(field.type()), field.name(), field.comment()) for field in fields
    ]))
    s += "\n"
    s += "public function __construct({0}) {{\n{1}\n}}".format(", ".join(arguments), "\n".join(assignments))

    return s


class SerializingField:
    def __init__(self, name: str, typ: str, serialized_name: str):
        self._name = name
        self._typ = typ
        self._serialized_name = serialized_name

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return self._typ

    def serialized_name(self) -> str:
        return self._serialized_name

    def convert_func(self) -> Optional[str]:
        return get_php_convert_func(self.type())


def generate_simple_serialize_method(method_name: str, fields: List[SerializingField]) -> str:
    elements = []

    for field in fields:
        lval = "$this->{0}".format(field.name())

        elements.append('"{0}" => {1}'.format(field.serialized_name(), lval))

    s = ""
    s += generate_comment(Comment(None, [
        ReturnAnnotation("array")
    ]))
    s += "\n"
    s += "public function {0}() {{\nreturn array({1});\n}}".format(
        method_name, ", ".join(elements)
    )

    return s


class DeserializingField:
    def __init__(self, position: int, typ: str, serialized_name: str):
        self._position = position
        self._typ = typ
        self._serialized_name = serialized_name

    def position(self) -> int:
        return self._position

    def type(self) -> str:
        return self._typ

    def serialized_name(self) -> str:
        return self._serialized_name

    def convert_func(self) -> Optional[str]:
        return get_php_convert_func(self.type())


def generate_simple_deserialize_method(method_name: str, clazz: str, n: int, fields: List[DeserializingField]) -> str:
    arguments = []

    for _ in range(n):
        arguments.append('null')

    for field in fields:
        lval = '$json["{0}"]'.format(field.serialized_name())

        if field.convert_func() is not None:
            lval = field.convert_func().format(expr=lval)

        arguments[field.position()] = "isset({0}) ? {1} : null".format(
            '$json["{0}"]'.format(field.serialized_name()), lval
        )

    s = ""
    s += generate_comment(Comment(None, [
        ParamAnnotation("array", "json"),
        ReturnAnnotation(clazz)
    ]))
    s += "\n"
    s += "public static function {0}($json) {{\nreturn new {1}({2});\n}}".format(
        method_name, clazz, ", ".join(arguments)
    )

    return s


def generate_to_array_method(fields: List[Field]) -> str:
    return generate_simple_serialize_method('toArray', [
        SerializingField(x.name(), x.type(), x.name()) for x in fields
    ])


def generate_from_array_method(clazz: str, fields: List[Field]) -> str:
    n = len(fields)

    return generate_simple_deserialize_method("fromArray", clazz, n, [
        DeserializingField(pos, fields[pos].type(), fields[pos].name()) for pos in range(n)
    ])


def generate_group_serialize_methods(fields: List[Field]) -> List[str]:
    aggregate = aggregate_groups_from_fields(fields)
    methods = []

    for item in aggregate:
        group_name = item[1]
        fields = item[2]

        method_name = 'to' + upper_first(group_name)

        methods.append(generate_simple_serialize_method(method_name, [
            SerializingField(field[1].name(), field[1].type(), field[2].member()) for field in fields
        ]))

    return methods


def generate_group_deserialize_methods(clazz: str, fields: List[Field]) -> List[str]:
    aggregate = aggregate_groups_from_fields(fields)
    methods = []

    for item in aggregate:
        n = item[0]
        group_name = item[1]
        fields = item[2]

        method_name = 'from' + upper_first(group_name)

        methods.append(generate_simple_deserialize_method(method_name, clazz, n, [
            DeserializingField(field[0], field[1].type(), field[2].member()) for field in fields
        ]))

    return methods


def generate_serialize_methods(spec: Spec) -> str:
    methods = [
        generate_to_array_method(spec.fields()),
        *generate_group_serialize_methods(spec.fields()),
    ]

    return '\n\n'.join(methods)


def generate_deserialize_methods(spec: Spec) -> str:
    methods = [
        generate_from_array_method(spec.lang().php().clazz(), spec.fields()),
        *generate_group_deserialize_methods(spec.lang().php().clazz(), spec.fields()),
    ]

    return '\n\n'.join(methods)


class PHPGenerator(Generator):
    @staticmethod
    def get_extension() -> str:
        return '.php'

    @staticmethod
    def get_clazz(spec: Spec) -> str:
        return spec.lang().php().clazz()

    def generate(self, spec: Spec, fp: IO) -> None:
        print(
            Fore.GREEN + "[DEBUG] class '{0}\\{1}' is being generated...".format(
                spec.lang().php().namespace(),
                spec.lang().php().clazz()
            ) + Fore.RESET)

        tpl_args = {
            "namespace": spec.lang().php().namespace(),
            "clazz": spec.lang().php().clazz(),
            "members": generate_members(spec.fields()),
            "constructor": generate_constructor(spec.fields()),
            "deserializers": generate_deserialize_methods(spec),
            "serializers": generate_serialize_methods(spec),
        }
        s = TEMPLATE.format(**tpl_args)
        fp.write(s)

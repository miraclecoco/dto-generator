from typing import List, Optional, Dict, Tuple
from colorama import Fore

from internal.spec import Field, Spec, Group
from internal.gen import Generator
from internal.lang.php import Comment, VarAnnotation, ReturnAnnotation, ParamAnnotation


def upper_first(s: str):
    return s[0:1].upper() + s[1:]


def code(s: str) -> str:
    return s.strip()


TEMPLATE = code("""
<?php

// THIS FILE IS AUTO GENERATED

namespace {namespace};

class {clazz} {{
{properties}

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
}

PHP_TYPE_FN = {
    "string": "strval",
    "int": "intval",
    "float": "floatval",
    "double": "doubleval",
    "bool": "boolval",
}


def get_php_type(typ: str) -> str:
    return PHP_TYPE[typ] if typ in PHP_TYPE else typ


def get_php_type_fn(typ: str) -> Optional[str]:
    if get_php_type(typ) not in PHP_TYPE_FN:
        return None

    return PHP_TYPE_FN[get_php_type(typ)]


def generate_comment(comment: Comment) -> str:
    if not comment.needs_generate():
        return ""

    lines = []

    if comment.docstring() is not None:
        lines.append("{0}".format(comment.docstring()))
        lines.append("")

    for annotation in comment.annotations():
        lines.append("@{0} {1}".format(annotation.name(), annotation.value()))

    s = ""
    s += "/**\n"
    s += " * " + "\n * ".join(lines) + "\n"
    s += " */"

    return s


def generate_class_member(field: Field) -> str:
    s = ""
    s += generate_comment(Comment(
        field.comment(), [
            VarAnnotation(get_php_type(field.type()))
        ]
    ))
    s += "\n"
    s += "public ${0};".format(field.name())

    return s


def generate_multi_class_members(fields: List[Field]) -> str:
    members = []

    for field in fields:
        members.append(generate_class_member(field))

    return "\n\n".join(members)


def generate_constructor(fields: List[Field]) -> str:
    arguments = []
    assignments = []

    for field in fields:
        arguments.append("${0}".format(field.name()))
        assignments.append("$this->{0} = ${1};".format(field.name(), field.name()))

    s = ""
    s += generate_comment(Comment(
        "Constructor", [
            ParamAnnotation(get_php_type(field.type()), field.name(), field.comment()) for field in fields
        ]
    ))
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
        return get_php_type_fn(self.type())


def generate_simple_serialize_method(method_name: str, fields: List[SerializingField]) -> str:
    elements = []

    for field in fields:
        if field.convert_func() is not None:
            elements.append("\"{0}\" => {1}($this->{2})".format(
                field.serialized_name(), field.convert_func(), field.name()
            ))
        else:
            elements.append("\"{0}\" => $this->{1},".format(field.serialized_name(), field.name()))

    s = ""
    s += generate_comment(Comment(None, [
        ReturnAnnotation("array")
    ]))
    s += "\n"
    s += "public function {0}() {{\n".format(method_name)
    s += "return array(\n{0}\n);\n".format(", \n".join(elements))
    s += "}"

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
        return get_php_type_fn(self.type())


def generate_simple_deserialize_method(method_name: str, clazz: str, n: int, fields: List[DeserializingField]) -> str:
    arguments = []

    for _ in range(n):
        arguments.append('null')

    for field in fields:
        if field.convert_func() is not None:
            arguments[field.position()] = "{0}($json[\"{1}\"])".format(field.convert_func(), field.serialized_name())
        else:
            arguments[field.position()] = "$json[\"{0}\"]".format(field.serialized_name())

    s = ""
    s += generate_comment(Comment(None, [
        ParamAnnotation("array", "json"),
        ReturnAnnotation(clazz)
    ]))
    s += "\n"
    s += "public static function {0}($json) {{\n".format(method_name)
    s += "return new {0}({1});\n".format(clazz, ", ".join(arguments))
    s += "}"

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


def aggregate_groups_from_fields(fields: List[Field]) -> List[Tuple[int, str, List[Tuple[int, Field, Group]]]]:
    bucket = {}  # type: Dict[str, Tuple[int, str, List[Tuple[int, Field, Group]]]]

    n = len(fields)
    for pos in range(n):
        field = fields[pos]

        if field.groups() is not None:
            for group in field.groups():
                if group.name() not in bucket:
                    bucket[group.name()] = (n, group.name(), [])

                bucket[group.name()][2].append((pos, field, group))

    return list(bucket.values())


def generate_serializers_by_group(fields: List[Field]) -> List[str]:
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


def generate_deserializers_by_group(clazz: str, fields: List[Field]) -> List[str]:
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


def generate_serializers(spec: Spec) -> str:
    methods = [
        generate_to_array_method(spec.fields()),
        *generate_serializers_by_group(spec.fields()),
    ]

    return '\n\n'.join(methods)


def generate_deserializers(spec: Spec) -> str:
    methods = [
        generate_from_array_method(spec.source().clazz(), spec.fields()),
        *generate_deserializers_by_group(spec.source().clazz(), spec.fields()),
    ]

    return '\n\n'.join(methods)


class PHPGenerator(Generator):
    def __init__(self):
        pass

    def generate(self, spec: Spec) -> str:
        print(
            Fore.GREEN + "[DEBUG] class '{0}\\{1}' is being generated...".format(
                spec.source().namespace(),
                spec.source().clazz()
            ) + Fore.RESET)

        tpl_args = {
            "namespace": spec.source().namespace(),
            "clazz": spec.source().clazz(),
            "properties": generate_multi_class_members(spec.fields()),
            "constructor": generate_constructor(spec.fields()),
            "deserializers": generate_deserializers(spec),
            "serializers": generate_serializers(spec),
        }
        return TEMPLATE.format(**tpl_args)

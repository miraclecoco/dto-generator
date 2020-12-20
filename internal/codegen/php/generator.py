from typing import List, Optional, IO, Tuple
from colorama import Fore

from internal.codegen.php.convension import AccessModifier
from internal.spec import Field, Spec, aggregate_groups_from_fields
from internal.codegen import Generator
from internal.util import upper_first
from internal.lang.php import Comment, VarAnnotation, ReturnAnnotation, ParamAnnotation
from internal.codegen.php.ast import Type, Identifier, StatementBlock
from internal.codegen.php.expr import SourceFile
from internal.codegen.php.element import VariableDeclaration, FunctionDeclaration, \
    ArgumentListDeclaration, ArgumentDeclaration, ParameterList, Parameter
from internal.codegen.php.extension import DocCommentStatement, Annotation
from internal.codegen.php.grammer import ClassDeclaration, MemberDeclaration, MethodDeclaration, \
    UnaryAssignmentStatement, \
    ThisAccessor, Scope, AnyEvaluation, \
    Accessor, NamespaceDeclaration, InvocationStatement, NamedCallableReference, MethodBody, ReturnStatement, \
    ArrayDeclaration, ArrayElementDeclaration


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
    "datetime": "\\DateTimeImmutable",
    "any": "mixed",
}

PHP_SERIALIZE_FN = {
    "datetime": "{expr}->getTimestamp()"
}

PHP_DESERIALIZE_FN = {
    "string": "strval({expr})",
    "integer": "intval({expr})",
    "float": "floatval({expr})",
    "double": "doubleval({expr})",
    "boolean": "boolval({expr})",
    "datetime": '\\date_create_immutable(date("Y-m-d H:i:s", (is_numeric({expr}) ? {expr} : strtotime({expr}))))'
}


def get_php_type(typ: str) -> str:
    return PHP_TYPE[typ] if typ in PHP_TYPE else typ


def get_php_serialize_func(typ: str) -> Optional[str]:
    return PHP_SERIALIZE_FN[typ] if typ in PHP_SERIALIZE_FN else None


def get_php_deserialize_func(typ: str) -> Optional[str]:
    return PHP_DESERIALIZE_FN[typ] if typ in PHP_DESERIALIZE_FN else None


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
    comment = Comment(field.comment(), [
        VarAnnotation(get_php_type(field.type()))
    ])

    s = ""
    if comment.needs_generate():
        s += generate_comment(comment)
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

    comment = Comment(None, [
        ParamAnnotation(get_php_type(field.type()), field.name(), field.comment()) for field in fields
    ])

    s = ""

    if comment.needs_generate():
        s += generate_comment(comment)
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
        return get_php_serialize_func(self.type())


def generate_simple_serialize_method(method_name: str, fields: List[SerializingField]) -> str:
    elements = []

    for field in fields:
        lval = '$this->{0}'.format(field.name())
        substituted_lval = lval

        if field.convert_func() is not None:
            substituted_lval = field.convert_func().format(expr=substituted_lval)

        elements.append('"{0}" => {1}'.format(
            field.serialized_name(), "is_null({0}) ? null : {1}".format(lval, substituted_lval)
        ))

    comment = Comment(None, [
        ReturnAnnotation("array")
    ])

    s = ""

    if comment.needs_generate():
        s += generate_comment(comment)
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
        return get_php_deserialize_func(self.type())


def generate_simple_deserialize_method(method_name: str, clazz: str, n: int, fields: List[DeserializingField]) -> str:
    arguments = []

    for _ in range(n):
        arguments.append('null')

    for field in fields:
        lval = '$json["{0}"]'.format(field.serialized_name())
        substituted_lval = lval

        if field.convert_func() is not None:
            substituted_lval = field.convert_func().format(expr=substituted_lval)

        arguments[field.position()] = "isset({0}) ? {1} : null".format(lval, substituted_lval)

    comment = Comment(None, [
        ParamAnnotation("array", "json"),
        ReturnAnnotation(clazz)
    ])

    s = ""

    if comment.needs_generate():
        s += generate_comment(comment)
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


def v1_generate_members(spec: Spec) -> List[StatementBlock]:
    class_fields = []

    for field in spec.fields():
        class_fields.append(DocCommentStatement(
            field.comment(), [
                Annotation.types(field.type())
            ]
        ))
        class_fields.append(MemberDeclaration(
            Identifier(field.name()), Type(field.type()), AccessModifier.public(), False
        ))

    return class_fields


def v1_generate_simple_serialize_method(method_name: str, fields: List[SerializingField]) -> List[StatementBlock]:
    arr_elements = []

    for field in fields:
        lval = '$this->{0}'.format(field.name())
        substituted_lval = lval

        if field.convert_func() is not None:
            substituted_lval = field.convert_func().format(expr=substituted_lval)

        arr_elements.append(ArrayElementDeclaration(
            field.serialized_name(),
            AnyEvaluation("is_null({0}) ? null : {1}".format(lval, substituted_lval), Type.any())
        ))

    class_fields = [
        DocCommentStatement(
            None, [
                Annotation.returns("array")
            ]
        ),
        MethodDeclaration(
            Identifier(method_name), Type.array(), AccessModifier.public(), False,
            ArgumentListDeclaration([]),
            MethodBody([
                ReturnStatement(ArrayDeclaration(True, arr_elements))
            ])
        )
    ]

    return class_fields


#
# TODO(dev):
#  use NewStatement instead NamedCallableReference
def v1_generate_simple_deserialize_method(
        method_name: str, clazz: str, n: int, fields: List[DeserializingField]
) -> List[StatementBlock]:
    parameters = []

    for index in range(n):
        parameters.append(AnyEvaluation("null", Type.any()))

    for field in fields:
        lval = '$data["{0}"]'.format(field.serialized_name())
        substituted_lval = lval

        if field.convert_func() is not None:
            substituted_lval = field.convert_func().format(expr=substituted_lval)

        parameters[field.position()] = AnyEvaluation(
            "isset({0}) ? {1} : null".format(lval, substituted_lval), Type(field.type())
        )

    class_fields = [
        DocCommentStatement(
            None, [
                Annotation.param("data", Type.dictionary().represent())
            ]
        ),
        MethodDeclaration(
            Identifier(method_name), Type(clazz), AccessModifier.public(), True,
            ArgumentListDeclaration([
                ArgumentDeclaration(Identifier("data"), Type.dictionary()),
            ]),
            MethodBody([
                ReturnStatement(
                    InvocationStatement(
                        NamedCallableReference("new {0}".format(clazz)), Type(clazz),
                        ParameterList(parameters)
                    )
                )
            ])
        )
    ]

    return class_fields


def v1_generate_to_array_method(fields: List[Field]) -> List[StatementBlock]:
    return v1_generate_simple_serialize_method('toArray', [
        SerializingField(x.name(), x.type(), x.name()) for x in fields
    ])


def v1_generate_from_array_method(clazz: str, fields: List[Field]) -> List[StatementBlock]:
    n = len(fields)

    return v1_generate_simple_deserialize_method("fromArray", clazz, n, [
        DeserializingField(pos, fields[pos].type(), fields[pos].name()) for pos in range(n)
    ])


def v1_generate_group_serializing_methods(fields: List[Field]) -> List[StatementBlock]:
    aggregation = aggregate_groups_from_fields(fields)
    stmts = []

    for item in aggregation:
        group_name = item[1]
        fields = item[2]

        method_name = 'to' + upper_first(group_name)

        stmts.extend(v1_generate_simple_serialize_method(method_name, [
            SerializingField(field[1].name(), field[1].type(), field[2].member()) for field in fields
        ]))

    return stmts


def v1_generate_group_deserializing_methods(clazz: str, fields: List[Field]) -> List[StatementBlock]:
    aggregation = aggregate_groups_from_fields(fields)
    stmts = []

    for item in aggregation:
        n = item[0]
        group_name = item[1]
        fields = item[2]

        method_name = 'from' + upper_first(group_name)

        stmts.extend(v1_generate_simple_deserialize_method(method_name, clazz, n, [
            DeserializingField(field[0], field[1].type(), field[2].member()) for field in fields
        ]))

    return stmts


class PHPGenerator(Generator):
    @staticmethod
    def get_extension() -> str:
        return '.php'

    @staticmethod
    def get_clazz(spec: Spec) -> str:
        return spec.lang().php().clazz()

    def generate(self, spec: Spec, fp: IO) -> None:
        file = SourceFile([
            NamespaceDeclaration(spec.lang().php().namespace()),
            ClassDeclaration(Identifier(spec.lang().php().clazz()), [
                *v1_generate_members(spec),
                *v1_generate_from_array_method(spec.lang().php().clazz(), spec.fields()),
                *v1_generate_group_deserializing_methods(spec.lang().php().clazz(), spec.fields()),
                *v1_generate_to_array_method(spec.fields()),
                *v1_generate_group_serializing_methods(spec.fields())
            ])
        ])
        print(file.print())

    def generate_old(self, spec: Spec, fp: IO) -> None:
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

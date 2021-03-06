from typing import IO, List, Optional
from colorama import Fore

from internal.lang.ts import Comment, ParamAnnotation
from internal.spec import Spec, Field, aggregate_groups_from_fields
from internal.codegen import Generator
from internal.util import upper_first
from internal.codegen.ts.ast import Type
from internal.codegen.ts.expr import SourceFile
from internal.codegen.ts.element import AccessModifier, StaticModifier, VariableDeclaration, FunctionDeclaration, \
    ArgumentList, Argument
from internal.codegen.ts.extension import DocComment, Annotation
from internal.codegen.ts.grammer import Class, Member, Method, UnaryAssignment, ThisAccessor, Scope, AnyEvaluation, \
    Accessor


def code(s: str) -> str:
    return s.strip()


TEMPLATE = code("""
// THIS FILE IS AUTO GENERATED

/* eslint-disable */

export class {clazz} {{
{members}

{constructor}

{deserializers}

{serializers}
}}
""") + "\n"

TS_TYPE = {
    "string": "string",
    "integer": "number",
    "float": "number",
    "double": "number",
    "boolean": "boolean",
    "datetime": "Date",
    "any": "any",
}

TS_SERIALIZE_FN = {
    "datetime": "{expr}.getSeconds()"
}

TS_DESERIALIZE_FN = {
    "string": "({expr}).toString()",
    "integer": "parseInt({expr})",
    "float": "parseFloat({expr})",
    "double": "parseFloat({expr})",
    "boolean": "!!({expr})",
    "datetime": "new Date(parseInt({expr}) * 1000)"
}


def get_ts_type(typ: str) -> 'str':
    return TS_TYPE[typ] if typ in TS_TYPE else typ


def get_ts_serialize_func(typ: str) -> Optional['str']:
    return TS_SERIALIZE_FN[typ] if typ in TS_SERIALIZE_FN else None


def get_ts_deserialize_func(typ: str) -> Optional['str']:
    return TS_DESERIALIZE_FN[typ] if typ in TS_DESERIALIZE_FN else None


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
            lines.append("@{0} {1}".format(annotation.identifier(), annotation.value()))

    s = ""
    s += "/**\n"
    s += " * {0}\n".format("\n * ".join(lines))
    s += " */"

    return s


def generate_member(field: Field) -> 'str':
    comment = Comment(field.comment())
    s = ""

    if comment.needs_generate():
        s += generate_comment(comment)
        s += "\n"

    s += "public {0}: {1};".format(field.name(), get_ts_type(field.type()))

    return s


def generate_members(fields: List[Field]):
    members = []

    for field in fields:
        members.append(generate_member(field))

    return "\n\n".join(members)


def generate_constructor(fields: List[Field]):
    arguments = []
    assignments = []

    for field in fields:
        arguments.append("{0}: {1}".format(field.name(), get_ts_type(field.type())))
        assignments.append("this.{0} = {0};".format(field.name()))

    comment = Comment(None, [
        ParamAnnotation(field.name(), field.comment()) for field in fields
    ])

    s = ""

    if comment.needs_generate():
        s += generate_comment(comment)
        s += "\n"

    s += "public constructor({0}) {{\n{1}\n}}".format(", ".join(arguments), "\n".join(assignments))

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
        return get_ts_serialize_func(self.type())


def generate_simple_serialize_method(method_name: str, fields: List[SerializingField]) -> str:
    elements = []

    for field in fields:
        lval = "this.{0}".format(field.name())
        substituted_lval = lval

        if field.convert_func() is not None:
            substituted_lval = field.convert_func().format(expr=substituted_lval)

        elements.append("\"{0}\": {1}".format(
            field.serialized_name(), "{0} === null ? null : {1}".format(lval, substituted_lval)
        ))

    s = ""
    s += "public {0}(): any {{\nreturn {{{1}}};\n}}".format(
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
        return get_ts_deserialize_func(self.type())


def generate_simple_deserialize_method(method_name: str, clazz: str, n: int, fields: List[DeserializingField]) -> str:
    arguments = []

    for _ in range(n):
        arguments.append('null')

    for field in fields:
        lval = 'json["{0}"]'.format(field.serialized_name())
        substituted_lval = lval

        if field.convert_func() is not None:
            substituted_lval = field.convert_func().format(expr=substituted_lval)

        arguments[field.position()] = "{0}.hasOwnProperty('{1}') ? {2} : null".format(
            'json', field.serialized_name(), substituted_lval
        )

    s = ""
    s += "public static {0}(json: any): {1} {{\nreturn new {1}({2});\n}}".format(
        method_name, clazz, ", ".join(arguments)
    )

    return s


def generate_to_array_method(fields: List[Field]) -> str:
    return generate_simple_serialize_method('toObject', [
        SerializingField(x.name(), x.type(), x.name()) for x in fields
    ])


def generate_from_array_method(clazz: str, fields: List[Field]) -> str:
    n = len(fields)

    return generate_simple_deserialize_method("fromObject", clazz, n, [
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
        generate_from_array_method(spec.lang().ts().clazz(), spec.fields()),
        *generate_group_deserialize_methods(spec.lang().ts().clazz(), spec.fields()),
    ]

    return '\n\n'.join(methods)


class TSGenerator(Generator):
    @staticmethod
    def get_extension() -> str:
        return '.ts'

    @staticmethod
    def get_clazz(spec: Spec) -> str:
        return spec.lang().ts().clazz()

    def generate(self, spec: Spec, fp: IO) -> None:
        file = SourceFile([
            Class("MyClass", [
                DocComment("Member", [
                    Annotation.param("myProperty1", "This is a description")
                ]),
                Member([AccessModifier.public(), StaticModifier()], VariableDeclaration("myProperty1", Type.string())),
                Member([AccessModifier.public(), StaticModifier()],
                       VariableDeclaration("myProperty2", Type.instance("Date"))),
                Member([AccessModifier.public(), StaticModifier()], VariableDeclaration("myProperty3", Type.null())),
                Member([AccessModifier.public(), StaticModifier()],
                       VariableDeclaration("myProperty3", Type.undefined())),
                Method(
                    [AccessModifier.public()],
                    FunctionDeclaration("myMethod1", Type.instance("Date"), ArgumentList([
                        Argument("arg1", Type.string()),
                        Argument("arg2", Type.boolean()),
                        Argument("arg3", Type.instance("Date")),
                    ])),
                    [
                        UnaryAssignment(
                            Accessor.series([
                                ThisAccessor(Scope(Type.instance("MyClass"))),
                                Accessor("foo", Type.instance("Foo")),
                                Accessor("bar", Type.instance("Bar")),
                                Accessor("baz", Type.instance("Baz")),
                                Accessor("val", Type.string()),
                            ]), AnyEvaluation("123", Type.number()))
                    ]
                )
            ])
        ])
        print(file.print())

    def generate_old(self, spec: Spec, fp: IO) -> None:
        print(
            Fore.GREEN + "[DEBUG] class '{0}' is being generated...".format(
                spec.lang().ts().clazz()
            ) + Fore.RESET)

        s = TEMPLATE.format(**{
            "clazz": spec.lang().ts().clazz(),
            "members": generate_members(spec.fields()),
            "constructor": generate_constructor(spec.fields()),
            "deserializers": generate_deserialize_methods(spec),
            "serializers": generate_serialize_methods(spec),
        })
        fp.write(s)

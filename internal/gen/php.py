from typing import List, Optional, Dict, Tuple
from colorama import Fore

from internal.spec import Field, Spec, Group
from internal.gen import Generator
from internal.lang.php import Comment, VarAnnotation, ReturnAnnotation, ParamAnnotation


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
    # if not comment.needs_generate():
    # return ""

    s = ""
    s += "/**\n"

    if comment.docstring() is not None:
        s += " * {0}\n".format(comment.docstring())
        s += " *\n"

    for at in comment.annotations():
        s += " * @{0} {1}\n".format(at.name(), at.value())

    s += " */"

    return s


def generate_class_member(field: Field) -> str:
    s = ""
    s += generate_comment(Comment(
        field.comment(),
        [VarAnnotation(get_php_type(field.type()))]
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
    s = ""
    s += generate_comment(Comment(
        None, [
            ParamAnnotation(get_php_type(field.type()), field.name(), field.comment()) for field in fields
        ]
    ))
    s += "\n"

    args = ""
    assigns = ""

    for field in fields:
        args += "${0}, ".format(field.name())
        assigns += "$this->{0} = ${1};\n".format(field.name(), field.name())

    if args[-2:] == ", ":
        args = args[:-2]

    s += "public function __construct({0}) {{\n{1}}}".format(args, assigns)

    return s


def generate_simple_serialize_method(func_name: str, fields: List[Tuple[str, str, str]]) -> str:
    s = ""
    s += generate_comment(Comment(
        None, [
            ReturnAnnotation("array")
        ]
    ))
    s += "\n"
    s += "public function {0}() {{\n".format(func_name)

    assigns = ""
    for field in fields:
        fn = get_php_type_fn(field[0])
        var = field[1]
        key = field[2]

        if fn is not None:
            assigns += "\"{0}\" => {1}($this->{2}),\n".format(key, fn, var)
        else:
            assigns += "\"{0}\" => $this->{1},\n".format(key, var)

    if assigns[-2:] == ",\n":
        assigns = assigns[:-2] + "\n"

    s += "return array(\n{0});\n".format(assigns)
    s += "}"

    return s


def generate_simple_deserialize_method(func_name: str, clazz: str, fields: List[Tuple[str, str]]) -> str:
    s = ""
    s += generate_comment(Comment(
        None, [
            ParamAnnotation("array", "json"),
            ReturnAnnotation(clazz)
        ]
    ))
    s += "\n"
    s += "public static function {0}($json) {{\n".format(func_name)

    args = ""
    for field in fields:
        fn = get_php_type_fn(field[0])

        if fn is not None:
            args += "{0}($json[\"{1}\"]), ".format(fn, field[1])
        else:
            args += "$json[\"{0}\"], ".format(field[1])

    if args[-2:] == ", ":
        args = args[:-2]

    s += "return new {0}({1});\n".format(clazz, args)
    s += "}"

    return s


def generate_to_array_method(fields: List[Field]) -> str:
    return generate_simple_serialize_method('toArray', [(x.type(), x.name(), x.name()) for x in fields])


def generate_from_array_method(clazz: str, fields: List[Field]) -> str:
    return generate_simple_deserialize_method("fromArray", clazz, [(x.type(), x.name()) for x in fields])


def aggregate_groups_from_fields(fields: List[Field]) -> Dict[str, List[Tuple[Group, Field]]]:
    bucket = {}

    for field in fields:
        if field.groups() is not None:
            for group in field.groups():
                if group.name() not in bucket:
                    bucket[group.name()] = []

                bucket[group.name()].append((group, field))

    return bucket


def generate_serializers_by_alias(fields: List[Field]) -> List[str]:
    ag = aggregate_groups_from_fields(fields)
    methods = []

    for item in ag.items():
        group_name = item[0]
        tups = item[1]

        func_name = 'to' + group_name[0:1].upper() + group_name[1:]

        methods.append(
            generate_simple_serialize_method(func_name,
                                             [(tup[1].type(), tup[1].name(), tup[0].member()) for tup in tups]))

    return methods


def generate_deserializers_by_alias(clazz: str, fields: List[Field]) -> List[str]:
    ag = aggregate_groups_from_fields(fields)
    methods = []

    for item in ag.items():
        group_name = item[0]
        tups = item[1]

        func_name = 'from' + group_name[0:1].upper() + group_name[1:]

        methods.append(
            generate_simple_deserialize_method(func_name, clazz, [(tup[1].type(), tup[1].name()) for tup in tups]))

    return methods


def generate_serializers(spec: Spec) -> str:
    methods = [
        generate_to_array_method(spec.fields()),
        *generate_serializers_by_alias(spec.fields()),
    ]

    return '\n\n'.join(methods)


def generate_deserializers(spec: Spec) -> str:
    methods = [
        generate_from_array_method(spec.source().clazz(), spec.fields()),
        *generate_deserializers_by_alias(spec.source().clazz(), spec.fields()),
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

from typing import List
from colorama import Fore

from internal.spec import Field, Spec
from internal.gen import Generator
from internal.lang.php import Comment, VarAnnotation, ReturnAnnotation


def code(s: str) -> str:
    return s.strip()


TEMPLATE = code("""
<?php

// THIS FILE IS AUTO GENERATED

namespace {namespace};

class {clazz} {{
{properties}

{constructor}

{fromJson}

{toJson}
}}
""") + "\n"

PHP_TYPES = {
    "integer": "int",
    "float": "float",
    "double": "double",
    "string": "string",
    "boolean": "bool",
}


def get_php_type(typ: str):
    return PHP_TYPES[typ] if typ in PHP_TYPES else typ


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
        [VarAnnotation(get_php_type(field.typ()))]
    ))
    s += "\n"
    s += "public ${0};".format(field.name())

    return s


def generate_multi_class_members(fields: List[Field]) -> str:
    s = ""

    for field in fields:
        s += "{0}\n\n".format(generate_class_member(field))

    if s[-2:] == "\n\n":
        s = s[:-2]

    return s


def generate_constructor(fields: List[Field]) -> str:
    s = ""
    s += generate_comment(Comment(
        None,
        [VarAnnotation(
            get_php_type(field.typ()),
            field.name(),
            field.comment()
        ) for field in fields]
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


def generate_from_json_method(clazz: str, fields: List[Field]) -> str:
    s = ""
    s += generate_comment(Comment(
        None, [
            VarAnnotation("array", "json"),
            ReturnAnnotation(clazz)
        ]
    ))
    s += "\n"
    s += "public static function fromJson($json) {\n"

    args = ""
    for field in fields:
        args += "$json[\"{0}\"], ".format(field.name())

    if args[-2:] == ", ":
        args = args[:-2]

    s += "return new {0}({1});\n".format(clazz, args)
    s += "}"

    return s


def generate_to_json_method(fields: List[Field]) -> str:
    s = ""
    s += generate_comment(Comment(
        None, [
            ReturnAnnotation("array")
        ]
    ))
    s += "\n"
    s += "public function toJson() {\n"

    assigns = ""
    for field in fields:
        k = field.name()
        assigns += "\"{0}\" => $this->{1},\n".format(k, k)

    if assigns[-2:] == ",\n":
        assigns = assigns[:-2] + "\n"

    s += "return array(\n{0});\n".format(assigns)
    s += "}"

    return s


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
            "fromJson": generate_from_json_method(spec.source().clazz(), spec.fields()),
            "toJson": generate_to_json_method(spec.fields())
        }
        return TEMPLATE.format(**tpl_args)

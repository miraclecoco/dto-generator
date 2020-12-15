import json
from copy import deepcopy
from typing import List, Optional, Tuple, Dict

from internal.util import check_key


class PHPLang:
    def __init__(self, namespace: str, clazz: str) -> None:
        self._namespace = namespace
        self._clazz = clazz

    @staticmethod
    def parse(conf: dict) -> 'PHPLang':
        check_key(conf, "namespace")
        check_key(conf, "clazz")

        return PHPLang(conf["namespace"], conf["clazz"])

    def namespace(self) -> str:
        return self._namespace

    def clazz(self) -> str:
        return self._clazz


class TSLang:
    def __init__(self, clazz: str):
        self._clazz = clazz

    @staticmethod
    def parse(conf: dict) -> 'TSLang':
        check_key(conf, 'clazz')

        return TSLang(conf['clazz'])

    def clazz(self) -> 'str':
        return self._clazz


class Lang:
    def __init__(self, php: PHPLang = None, ts: TSLang = None):
        self._php = php
        self._ts = ts

    @staticmethod
    def parse(conf: dict) -> 'Lang':
        if "php" not in conf:
            conf["php"] = None
        else:
            conf["php"] = PHPLang.parse(conf["php"])

        if "ts" not in conf:
            conf["ts"] = None
        else:
            conf["ts"] = TSLang.parse(conf["ts"])

        return Lang(conf["php"], conf["ts"])

    def php(self) -> 'PHPLang':
        return self._php

    def ts(self) -> 'TSLang':
        return self._ts


class Group:
    def __init__(self, name: str, member: str):
        self._name = name
        self._member = member

    @staticmethod
    def parse(conf: dict):
        check_key(conf, "name")
        check_key(conf, "member")

        return Group(conf["name"], conf["member"])

    def name(self) -> str:
        return self._name

    def member(self) -> str:
        return self._member


class Field:
    def __init__(self, name: str, typ: str, comment: str = None, groups: List[Group] = None) -> None:
        self._name = name
        self._typ = typ
        self._comment = comment
        self._groups = groups

    @staticmethod
    def parse(conf: dict) -> 'Field':
        check_key(conf, "name")
        check_key(conf, "type")

        if "comment" not in conf or not conf["comment"]:
            conf["comment"] = None

        if "groups" not in conf:
            conf["groups"] = None
        else:
            conf["groups"] = [Group.parse(x) for x in conf["groups"]]

        return Field(conf["name"], conf["type"], conf["comment"], conf["groups"])

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return self._typ

    def comment(self) -> Optional[str]:
        return self._comment

    def groups(self) -> Optional[List[Group]]:
        return self._groups


class Spec:
    def __init__(self, out_dir: str, lang: Lang, fields: List[Field]) -> None:
        self._out_dir = out_dir
        self._lang = lang
        self._fields = fields

    @staticmethod
    def parse(conf: dict) -> 'Spec':
        check_key(conf, "outDir")
        check_key(conf, "lang")
        check_key(conf, "fields")

        return Spec(
            conf["outDir"],
            Lang.parse(conf["lang"]),
            list(Field.parse(x) for x in conf["fields"])
        )

    def out_dir(self) -> str:
        return self._out_dir

    def lang(self) -> Lang:
        return self._lang

    def fields(self) -> List[Field]:
        return self._fields


def parse_file(spec_file: str):
    with open(spec_file, "r", encoding='utf8') as fp:
        spec_json = json.load(fp)

    return Spec.parse(deepcopy(spec_json))


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

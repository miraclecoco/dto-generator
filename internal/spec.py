import json
from typing import List, Optional

from .util import check_key


class Source:
    def __init__(self, namespace: str, clazz: str) -> None:
        self._namespace = namespace
        self._clazz = clazz

    @staticmethod
    def from_json(json: dict) -> 'Source':
        check_key(json, "namespace")
        check_key(json, "clazz")

        return Source(json["namespace"], json["clazz"])

    def namespace(self) -> str:
        return self._namespace

    def clazz(self) -> str:
        return self._clazz


class Group:
    def __init__(self, name: str, member: str):
        self._name = name
        self._member = member

    @staticmethod
    def from_json(json: dict):
        check_key(json, "name")
        check_key(json, "member")

        return Group(json["name"], json["member"])

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
    def from_json(json: dict) -> 'Field':
        check_key(json, "name")
        check_key(json, "type")

        if "commit" not in json:
            json["comment"] = None

        if "aliases" not in json:
            json["aliases"] = None

        if "groups" not in json:
            json["groups"] = None
        else:
            json["groups"] = [Group.from_json(x) for x in json["groups"]]

        return Field(json["name"], json["type"], json["comment"], json["groups"])

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return self._typ

    def comment(self) -> Optional[str]:
        return self._comment

    def groups(self) -> Optional[List[Group]]:
        return self._groups


class Spec:
    def __init__(self, out_dir: str, source: Source, fields: List[Field]) -> None:
        self._out_dir = out_dir
        self._source = source
        self._fields = fields

    @staticmethod
    def from_json(json: dict) -> 'Spec':
        check_key(json, "outDir")
        check_key(json, "source")
        check_key(json, "fields")

        return Spec(
            json["outDir"],
            Source.from_json(json["source"]),
            list(Field.from_json(x) for x in json["fields"])
        )

    def out_dir(self) -> str:
        return self._out_dir

    def source(self) -> Source:
        return self._source

    def fields(self) -> List[Field]:
        return self._fields


def parse_file(spec_file: str):
    with open(spec_file, "r", encoding='utf8') as fp:
        spec_json = json.load(fp)

    return Spec.from_json(spec_json)

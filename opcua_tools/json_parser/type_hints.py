from typing import List, TypedDict


class UANodeSetLine(TypedDict):
    elem_type: str
    tag: str


class NameSpaceURIsLine(TypedDict):
    elem_type: str
    uris: List[str]


class RequiredModelLine(TypedDict):
    publication_date: str
    uri: str
    version: str


class ModelLine(TypedDict):
    uri: str
    publication_date: str
    required_models: List[RequiredModelLine]
    version: str


class ModelsLine(TypedDict):
    elem_type: str
    uris: List[str]
    models: List[ModelLine]


class NodeIdLine(TypedDict):
    namespace: str
    type: str
    value: str


class AliasLine(TypedDict):
    name: str
    nodeid: NodeIdLine


class AliasesLine(TypedDict):
    elem_type: str
    aliases: List[AliasLine]

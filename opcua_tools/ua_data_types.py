# Copyright 2021 Prediktor AS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import ByteString, Optional, Tuple, Union
from dataclasses import dataclass, astuple
from datetime import datetime
from abc import ABC, abstractmethod
from base64 import b64encode
from enum import Enum
from xml.sax.saxutils import escape


class NodeIdType(Enum):
    NUMERIC = "i"
    STRING = "s"
    GUID = "g"
    OPAQUE = "b"

    def __repr__(self):
        return "NodeIdType" + "." + self.name


UAXMLNS_ATTRIB = 'xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"'


@dataclass(eq=True, frozen=True)
class UAData(ABC):
    pass

    @abstractmethod
    def xml_encode(self, include_xmlns: bool) -> str:
        pass

    def __lt__(self, other):
        return lt(self, other)

    def __gt__(self, other):
        return gt(self, other)

    def __le__(self, other):
        return le(self, other)

    def __ge__(self, other):
        return ge(self, other)


@dataclass(eq=True, frozen=True)
class DataTypeField(UAData):
    name: str
    value: str
    description: str

    def xml_encode(self, include_xmlns: bool) -> str:
        x = '<Field Name="' + self.name + '" Value="' + self.value + '"'
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        x += "<Description>" + self.description + "</Description>"
        x += "</Field>"
        return x


@dataclass(eq=True, frozen=True)
class DataTypeDefinition(UAData):
    name: str
    fields: Tuple[DataTypeField, ...]

    def xml_encode(self, include_xmlns: bool) -> str:
        encodedvalues = [v.xml_encode(include_xmlns=False) for v in self.fields]
        x = '<Definition Name="' + self.name + '"'
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + "\n".join(encodedvalues) + "</Definition>"
        return x


@dataclass(eq=True, frozen=True)
class UABuiltIn(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAInteger(UABuiltIn):  # TODO make unsigned / signed integers type
    value: Optional[int]


@dataclass(eq=True, frozen=True)
class UASByte(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<SByte"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</SByte>"
        return x


@dataclass(eq=True, frozen=True)
class UAByte(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UAByte"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</UAByte>"
        return x


@dataclass(eq=True, frozen=True)
class UAInt16(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Int16"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</Int16>"
        return x


@dataclass(eq=True, frozen=True)
class UAUInt16(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UInt16"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</UInt16>"
        return x


@dataclass(eq=True, frozen=True)
class UAInt32(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Int32"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</Int32>"
        return x


@dataclass(eq=True, frozen=True)
class UAUInt32(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UInt32"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</UInt32>"
        return x


@dataclass(eq=True, frozen=True)
class UAInt64(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Int64"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</Int64>"
        return x


@dataclass(eq=True, frozen=True)
class UAUInt64(UAInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UInt64"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</UInt64>"
        return x


@dataclass(eq=True, frozen=True)
class UAFloatingPoint(UABuiltIn):
    value: Optional[float]


@dataclass(eq=True, frozen=True)
class UAFloat(UAFloatingPoint):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Float"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</Float>"
        return x


@dataclass(eq=True, frozen=True)
class UADouble(UAFloatingPoint):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Double"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if self.value is not None else "") + "</Double>"
        return x


@dataclass(eq=True, frozen=True)
class UAString(UABuiltIn):
    value: Optional[str]

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<String"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (escape(str(self.value)) if self.value is not None else "")
            + "</String>"
        )
        return x


@dataclass(eq=True, frozen=True)
class UADateTime(UABuiltIn):
    value: datetime

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<DateTime"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (self.value.isoformat() if self.value is not None else "")
            + "</DateTime>"
        )
        return x


@dataclass(eq=True, frozen=True)
class UAGuid(UAString):
    pass


@dataclass(eq=True, frozen=True)
class UAByteString(UABuiltIn):
    value: Optional[ByteString]

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<ByteString "
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (b64encode(self.value).decode("utf-8") if self.value is not None else "")
            + "</ByteString>"
        )
        return x


@dataclass(eq=True, frozen=True)
class UABoolean(UABuiltIn):
    value: Optional[bool]

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Boolean "
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (
                ("true" if self.value is True else "false")
                if self.value is not None
                else ""
            )
            + "</Boolean>"
        )
        return x


@dataclass(eq=True, frozen=True)
class UAXMLElement(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UANodeId(UAData):
    namespace: int
    nodeid_type: NodeIdType
    value: str

    def __str__(self):
        if self.namespace == 0:
            return f"{self.nodeid_type.value}={self.value}"
        else:
            return f"ns={self.namespace};{self.nodeid_type.value}={self.value}"

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Identifier"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + self.__str__() + "</Identifier>"
        return x


@dataclass(eq=True, frozen=True)
class UAExpandedNodeId(UAString):
    value: Optional[str]


@dataclass(eq=True, frozen=True)
class UAStatusCode(UABuiltIn):
    value: int


@dataclass(eq=True, frozen=True)
class UADiagnosticInfo(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UAQualifiedName(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UALocalizedText(UABuiltIn):
    text: Optional[str]
    locale: Optional[str]

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<LocalizedText"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        x += "<Locale>" + (self.locale if self.locale is not None else "") + "</Locale>"
        x += "<Text>" + (escape(self.text) if self.text is not None else "") + "</Text>"
        x += "</LocalizedText>"
        return x


@dataclass(eq=True, frozen=True)
class UAVariant(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UADataValue(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UADecimal(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAEnumeration(UAInt32):
    string: str
    name: str


@dataclass(eq=True, frozen=True)
class UAArray(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAStructure(UAData):
    xmlstring: str

    def xml_encode(self, include_xmlns: bool) -> str:
        return self.xmlstring


@dataclass(eq=True, frozen=True)
class UAStructureOptionalField(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UnparsedUAExtensionObject(UABuiltIn):
    type_nodeid: Optional[UANodeId]
    body: Optional[Union[UAByteString, UAStructure]]

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<ExtensionObject"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        x += (
            "<TypeId>"
            + (
                self.type_nodeid.xml_encode(include_xmlns=False)
                if self.type_nodeid is not None
                else ""
            )
            + "</TypeId>"
        )
        x += (
            "<Body>"
            + (
                self.body.xml_encode(include_xmlns=False)
                if self.body is not None
                else ""
            )
            + "</Body>"
        )
        x += "</ExtensionObject>"
        return x


@dataclass(eq=True, frozen=True)
class UAEngineeringUnits(UAData):
    display_name: UALocalizedText
    description: UALocalizedText
    unit_id: int
    namespace_uri: str

    def xml_encode(self, include_xmlns: bool) -> str:
        body_contents = "<EUInformation>"
        body_contents += "<NamespaceUri>" + self.namespace_uri + "</NamespaceUri>"
        body_contents += "<UnitId>" + str(self.unit_id) + "</UnitId>"
        body_contents += "<DisplayName>"
        body_contents += (
            "<Locale>"
            + (
                self.display_name.locale
                if self.display_name.locale is not None
                else "en"
            )
            + "</Locale>"
        )
        body_contents += (
            "<Text>"
            + (self.display_name.text if self.display_name.text is not None else "")
            + "</Text>"
        )
        body_contents += "</DisplayName>"
        body_contents += "<Description>"
        body_contents += (
            "<Locale>"
            + (self.description.locale if self.description.locale is not None else "en")
            + "</Locale>"
        )
        body_contents += (
            "<Text>"
            + (self.description.text if self.description.text is not None else "")
            + "</Text>"
        )
        body_contents += "</Description>"
        body_contents += "</EUInformation>"

        # Todo fix hacky implementation
        return UnparsedUAExtensionObject(
            type_nodeid=UANodeId(0, NodeIdType.NUMERIC, "888"),
            body=UAStructure(xmlstring=body_contents),
        ).xml_encode(include_xmlns)


@dataclass(eq=True, frozen=True)
class UAEURange(UAData):
    low: float
    high: float

    def xml_encode(self, include_xmlns: bool) -> str:
        body_contents = "<Range>"
        body_contents += f"<Low>{self.low}</Low>"
        body_contents += f"<High>{self.high}</High>"
        body_contents += "</Range>"

        return UnparsedUAExtensionObject(
            type_nodeid=UANodeId(0, NodeIdType.NUMERIC, "885"),
            body=UAStructure(xmlstring=body_contents),
        ).xml_encode(include_xmlns)


@dataclass(eq=True, frozen=True)
class UAUnion(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAMessage(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAEmpty(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAListOf(UAData):
    value: Tuple[UAData, ...]
    typename: str

    def xml_encode(self, include_xmlns: bool) -> str:
        encodedvalues = []
        if self.value is not None:
            encodedvalues = [v.xml_encode(include_xmlns=False) for v in self.value]

        x = "<ListOf" + self.typename + " "
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + "".join(encodedvalues) + "</ListOf" + self.typename + ">"
        return x


def ge(u1: UAData, u2: UAData):
    return le(u1=u2, u2=u1)


def le(u1: UAData, u2: UAData):
    if u2 is None:
        return True
    ty1 = type(u1)
    ty2 = type(u2)
    if ty1 != ty2:
        return ty1.__name__ <= ty2.__name__

    t1 = str(astuple(u1))
    t2 = str(astuple(u2))

    return t1 <= t2


def gt(u1: UAData, u2: UAData):
    return lt(u1=u2, u2=u1)


def lt(u1: UAData, u2: UAData):
    if u2 is None:
        return True
    ty1 = type(u1)
    ty2 = type(u2)
    if ty1 != ty2:
        return ty1.__name__ < ty2.__name__

    t1 = str(astuple(u1))
    t2 = str(astuple(u2))

    return t1 < t2

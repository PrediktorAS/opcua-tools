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
import functools
import json
import math
import re
from abc import ABC, abstractmethod
from base64 import b64encode
from dataclasses import astuple, dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, ByteString, Optional, Tuple, Union
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd


class NodeIdType(Enum):
    NUMERIC = "i"
    STRING = "s"
    GUID = "g"
    OPAQUE = "b"

    def __repr__(self):
        return "NodeIdType" + "." + self.name


class VariantType(Enum):
    """The possible types of a variant."""

    Null = 0
    Boolean = 1
    SByte = 2
    Byte = 3
    Int16 = 4
    UInt16 = 5
    Int32 = 6
    UInt32 = 7
    Int64 = 8
    UInt64 = 9
    Float = 10
    Double = 11
    String = 12
    DateTime = 13
    Guid = 14
    ByteString = 15
    XmlElement = 16
    NodeId = 17
    ExpandedNodeId = 18
    StatusCode = 19
    QualifiedName = 20
    LocalizedText = 21
    ExtensionObject = 22
    DataValue = 23
    Variant = 24
    DiagnosticInfo = 25


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
    def resolve_builtin_type_number(self) -> int:
        class_name = self.__class__.__name__
        if class_name.startswith("UA"):
            class_name = class_name[2:]
        if class_name in VariantType.__members__:
            return VariantType[class_name].value
        else:
            raise ValueError(f"Unknown built-in type: {class_name}")


@dataclass(eq=True, frozen=True)
class UAInteger(UABuiltIn):
    value: int = pd.NA

    def __post_init__(self):
        if not pd.isna(self.value) and not isinstance(self.value, int):
            raise TypeError("Integer value must be an int")


@dataclass(eq=True, frozen=True)
class UASignedInteger(UAInteger):
    value: int = pd.NA


@dataclass(eq=True, frozen=True)
class UAUnsignedInteger(UAInteger):
    value: int = pd.NA

    def __post_init__(self):
        if not pd.isna(self.value) and not isinstance(self.value, int):
            raise TypeError("Integer value must be an int")
        if not pd.isna(self.value) and self.value < 0:
            raise ValueError("UnsignedInteger value cannot be negative")


@dataclass(eq=True, frozen=True)
class UASByte(UASignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<SByte"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</SByte>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAByte(UAUnsignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UAByte"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</UAByte>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAInt16(UASignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Int16"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</Int16>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAUInt16(UAUnsignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UInt16"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</UInt16>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAInt32(UASignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Int32"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</Int32>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAUInt32(UAUnsignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UInt32"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</UInt32>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAInt64(UASignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Int64"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</Int64>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        # Int64 and UInt64 are to be formatted as number encoded
        # as a JSON string according to spec
        if pd.isna(self.value):
            return None
        else:
            return '"' + str(float(self.value)) + '"'


@dataclass(eq=True, frozen=True)
class UAUInt64(UAUnsignedInteger):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<UInt64"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</UInt64>"
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        # Int64 and UInt64 are to be formatted as number encoded
        # as a JSON string according to spec
        if pd.isna(self.value):
            return None
        else:
            return '"' + str(float(self.value)) + '"'


@dataclass(eq=True, frozen=True)
class UAFloatingPoint(UABuiltIn):
    value: float = pd.NA

    def __post_init__(self):
        if self.value is not None:
            if not pd.isna(self.value) and not isinstance(
                self.value, (float, int, Decimal)
            ):
                raise TypeError(
                    "Floating Point Numbers value must be either be a float, int, or Decimal"
                )
        if isinstance(self.value, pd._libs.missing.NAType) or self.value is None:
            object.__setattr__(self, "value", pd.NA)
        else:
            object.__setattr__(self, "value", float(self.value))

    @functools.cache
    def json_encode(self) -> [str, None]:
        # According to the spec, special values are to be encoded as JSON
        # strings in the following manner
        special_floats_or_decimals = {
            None: None,
            pd.NA: None,
            float("inf"): '"Infinity"',
            float("-inf"): '"-Infinity"',
            float("nan"): "NaN",
        }
        if self.value in special_floats_or_decimals:
            return special_floats_or_decimals[self.value]
        elif math.isnan(self.value):
            return '"NaN"'
        else:
            return str(self.value)


@dataclass(eq=True, frozen=True)
class UAFloat(UAFloatingPoint):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Float"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</Float>"
        return x


@dataclass(eq=True, frozen=True)
class UADouble(UAFloatingPoint):
    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Double"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + (str(self.value) if not pd.isna(self.value) else "") + "</Double>"
        return x


@dataclass(eq=True, frozen=True)
class UAString(UABuiltIn):
    value: str = pd.NA

    def __post_init__(self):
        if not pd.isna(self.value) and not isinstance(self.value, str):
            raise TypeError("String value must be a string")
        if not (value := str(self.value)) or pd.isna(self.value):
            object.__setattr__(self, "value", pd.NA)
        else:
            object.__setattr__(self, "value", value)

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<String"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (escape(str(self.value)) if not pd.isna(self.value) else "")
            + "</String>"
        )
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return json.dumps(self.value, ensure_ascii=False)


@dataclass(eq=True, frozen=True)
class UADateTime(UABuiltIn):
    value: datetime = pd.NA

    def __post_init__(self):
        if not isinstance(self.value, datetime):
            raise TypeError("DateTime value must be a datetime object")

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<DateTime"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (
                self.value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                if not pd.isna(self.value)
                else ""
            )
            + "</DateTime>"
        )
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        """
        The time format used here is the recommended for RDF graphs
        is the format W3C is recommended. The format is:
        YYYY-MM-DDThh:mm:ss.sssTZD ex. 2023-05-08T14:30:00.000Z
        Is the same recommended format used by the OPC UA JSON encoding.
        """
        return '"' + self.value.strftime("%Y-%m-%dT%H:%M:%S.%fZ") + '"'


@dataclass(eq=True, frozen=True)
class UAGuid(UAString):
    pass


@dataclass(eq=True, frozen=True)
class UAByteString(UABuiltIn):
    value: ByteString = pd.NA

    def __post_init__(self):
        if not pd.isna(self.value) and not isinstance(self.value, ByteString):
            raise TypeError("ByteString value must be a ByteString object")
        object.__setattr__(self, "value", self.value if self.value else pd.NA)

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<ByteString"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (b64encode(self.value).decode("utf-8") if not pd.isna(self.value) else "")
            + "</ByteString>"
        )
        return x

    @functools.cache
    def json_encode(self):
        """ByteStryings are encoded as base64 strings in JSON, are enclosed
        in double quotes, and cannot contain illegal JSON characters.
        """
        if pd.isna(self.value) and not isinstance(self.value, ByteString):
            return None
        else:
            base64_string = b64encode(self.value).decode("utf-8")
            return json.dumps(base64_string, ensure_ascii=False)


@dataclass(eq=True, frozen=True)
class UABoolean(UABuiltIn):
    value: bool = pd.NA

    def __post_init__(self):
        if not pd.isna(self.value) and not isinstance(self.value, bool):
            raise TypeError("Boolean value must be a bool")

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Boolean"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += (
            ">"
            + (
                ("true" if self.value is True else "false")
                if not pd.isna(self.value)
                else ""
            )
            + "</Boolean>"
        )
        return x

    @functools.cache
    def json_encode(self) -> Union[str, None]:
        if pd.isna(self.value):
            return None
        else:
            return str(self.value).lower()


@dataclass(eq=True, frozen=True)
class UAXMLElement(UABuiltIn):
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("XMLElement value must be a string")

    def xml_encode(self, include_xmlns: bool) -> str:
        return self.value

    def json_encode(self) -> str:
        return json.dumps(self.value, ensure_ascii=False)


@dataclass(eq=True, frozen=True)
class UANodeId(UABuiltIn):
    namespace: int
    nodeid_type: NodeIdType
    value: Union[str, int]

    def __post_init__(self):
        if not isinstance(self.namespace, int):
            raise TypeError("Namespace must be an integer")
        if not isinstance(self.nodeid_type, (NodeIdType, int, str)):
            raise TypeError("NodeIdType must be a NodeIdType, int, or valid string")
        if not isinstance(self.value, (str, int)):
            raise TypeError("Value must be a string")

        # Casting into to Enum if int is passed
        if isinstance(self.nodeid_type, int):
            nodeid_type_symbol = self.nodeid_type_int_to_symbol(self.nodeid_type)
            object.__setattr__(self, "nodeid_type", NodeIdType(nodeid_type_symbol))

        # Casting into to Enum if string is passed
        if isinstance(self.nodeid_type, str):
            object.__setattr__(self, "nodeid_type", NodeIdType(self.nodeid_type))

        # Adding validation that the value is a valid NodeIdType based on the
        # value
        if self.nodeid_type == NodeIdType.NUMERIC:
            # Check if the value is a valid unsigned integer
            if not isinstance(self.value, (int, str)):
                raise TypeError(
                    f"Value must be an unsigned integer or string for NodeIdType {self.nodeid_type.value}"
                )
            if isinstance(self.value, str):
                if not self.value.isdigit():
                    raise TypeError(
                        f"Value must be an unsigned integer for NodeIdType {self.nodeid_type.value}"
                    )
                if self.value.startswith("-"):
                    raise TypeError(
                        f"Value must not start with 0 for NodeIdType {self.nodeid_type.value}"
                    )
                if self.value.startswith("0") and len(self.value) > 1:
                    raise TypeError(
                        f"Value must not start with 0 for NodeIdType {self.nodeid_type.value}"
                    )

    def __str__(self):
        if self.namespace == 0:
            return f"{self.nodeid_type.value}={self.value}"
        else:
            return f"ns={self.namespace};{self.nodeid_type.value}={self.value}"

    @staticmethod
    def nodeid_type_int_to_symbol(nodeid_type_int: int) -> str:
        nodeid_type_int_to_string = {0: "i", 1: "s", 2: "g", 3: "b"}
        if nodeid_type_int in nodeid_type_int_to_string:
            return nodeid_type_int_to_string[nodeid_type_int]
        raise TypeError(f"NodeIdType {nodeid_type_int} is not supported")

    def nodeid_type_value_to_int(self):
        nodeid_type_symbol_to_int = {"i": 0, "s": 1, "g": 2, "b": 3}
        if self.nodeid_type.value in nodeid_type_symbol_to_int:
            return nodeid_type_symbol_to_int[self.nodeid_type.value]
        raise TypeError(f"NodeIdType {self.nodeid_type.value} is not supported")

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Identifier"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + self.__str__() + "</Identifier>"
        return x

    def json_encode(self) -> str:
        nodeid_type_int = self.nodeid_type_value_to_int()
        json_content = ""
        # OPC UA Specification indicates Namespace field is omitted if it is 0
        if not self.namespace == 0:
            json_content = '"Namespace":' + str(self.namespace) + ","
        # OPC UA Specification indicates IdentifierType field is omitted if it is 0 (UInt32)
        if not nodeid_type_int == 0:
            json_content += '"IdType":' + str(nodeid_type_int) + ","
        # Properly encoding the identifier value based on datatype
        if self.nodeid_type is NodeIdType.NUMERIC:
            json_content += '"Id":' + str(self.value)
        else:  # "s", "g", "b"
            # If string, Guid identifier or byte string (Opaque) should treat value as string
            json_content += '"Id":' + '"' + str(self.value) + '"'

        return "{" + json_content + "}"


@dataclass(eq=True, frozen=True)
class UAExpandedNodeId(UAString):
    value: str = pd.NA


@dataclass(eq=True, frozen=True)
class UAStatusCode(UABuiltIn):
    value: int


@dataclass(eq=True, frozen=True)
class UADiagnosticInfo(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UAQualifiedName(UABuiltIn):
    namespace_index: np.uint16
    name: str

    def __post_init__(self):
        if not isinstance(self.namespace_index, int):
            raise TypeError("Namespace index must be an integer")
        if isinstance(self.namespace_index, int):
            if self.namespace_index < 0:
                raise ValueError("Namespace index must be a positive integer")
            object.__setattr__(self, "namespace_index", np.uint16(self.namespace_index))
        if not isinstance(self.name, str):
            raise TypeError("Name must be a string")

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<QualifiedName"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        x += "<NamespaceIndex>" + str(self.namespace_index) + "</NamespaceIndex>"
        x += "<Name>" + self.name + "</Name></QualifiedName>"
        return x

    def json_encode(self) -> str:
        json = ""
        json += '"Name":"' + self.name + '"'
        if not self.namespace_index == 0:
            json += ',"Uri":' + str(self.namespace_index)
        return "{" + json + "}"


@dataclass(eq=True, frozen=True)
class UALocalizedText(UABuiltIn):
    text: Optional[str] = pd.NA
    locale: Optional[str] = pd.NA

    def __post_init__(self):
        if (not isinstance(self.text, str)) and (not pd.isna(self.text)):
            raise TypeError("text must be a string or pd.NA")
        if (not isinstance(self.locale, str)) and (not pd.isna(self.locale)):
            raise TypeError("locale must be a string or pd.NA")
        if not pd.isna(self.locale):
            if not self.is_valid_locale(self.locale):
                raise ValueError(
                    "locale must be a valid locale string following the IETF RFC 5646 standard"
                )

    @staticmethod
    def is_valid_locale(locale_str: str):
        """Validates the format of the locale string using the IETF RFC 5646 standard
        The following regex is based on the regex provided by the IETF RFC 5646 standard
        and allows for the following formats:
        ^[a-zA-Z]{2,3}: 2-3 letter language code
        (?:[_-][a-zA-Z]{2,3}: optional 2-3 letter script code
        (?:[_-](?:\w{2,8}|\d{3}))?)?: optional 2-8 letter region code or 3 digit country code
        (?:\.[a-zA-Z0-9]{2,8})?$: optional variant code and optional extension code

        Args:
            locale_str (str): locale string to be validated

        Returns:
            bool: True if locale string is valid, False otherwise
        """

        if re.match(
            r"^[a-zA-Z]{2,3}(?:[_-][a-zA-Z]{2,3}(?:[_-](?:\w{2,8}|\d{3}))?)?(?:\.[a-zA-Z0-9]{2,8})?$",
            locale_str,
        ):
            return True
        else:
            return False

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<LocalizedText"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        x += (
            "<Locale>" + (self.locale if not pd.isna(self.locale) else "") + "</Locale>"
        )
        x += (
            "<Text>" + (escape(self.text) if not pd.isna(self.text) else "") + "</Text>"
        )
        x += "</LocalizedText>"
        return x

    def json_encode(self, input_locale: Optional[str] = None) -> Union[str, None]:
        json_content = ""

        if pd.isna(self.text):
            json_content += '"Text":' + json.dumps("", ensure_ascii=False)
        else:
            json_content += '"Text":' + json.dumps(self.text, ensure_ascii=False)

        if not pd.isna(input_locale):
            json_content += ',"Locale":' + json.dumps(input_locale, ensure_ascii=False)
        elif not pd.isna(self.locale):
            json_content += ',"Locale":' + json.dumps(self.locale, ensure_ascii=False)

        json_content = "{" + json_content + "}"
        return json_content


@dataclass(eq=True, frozen=True)
class UAVariant(UABuiltIn):
    value: Any = pd.NA
    type: VariantType = VariantType.Null

    def __post_init__(self):
        ua_class_type_to_variant_type = {
            UABoolean: VariantType.Boolean,
            UASByte: VariantType.SByte,
            UAByte: VariantType.Byte,
            UAInt16: VariantType.Int16,
            UAUInt16: VariantType.UInt16,
            UAInt32: VariantType.Int32,
            UAEnumeration: VariantType.Int32,
            UAUInt32: VariantType.UInt32,
            UAInt64: VariantType.Int64,
            UAUInt64: VariantType.UInt64,
            UAFloat: VariantType.Float,
            UADouble: VariantType.Double,
            UAString: VariantType.String,
            UADateTime: VariantType.DateTime,
            UAGuid: VariantType.Guid,
            UAByteString: VariantType.ByteString,
            UAXMLElement: VariantType.XmlElement,
            UANodeId: VariantType.NodeId,
            UAExpandedNodeId: VariantType.ExpandedNodeId,
            UAStatusCode: VariantType.StatusCode,
            UAQualifiedName: VariantType.QualifiedName,
            UALocalizedText: VariantType.LocalizedText,
            UAExtensionObject: VariantType.ExtensionObject,
            UADataValue: VariantType.DataValue,
            UAVariant: VariantType.Variant,
            UADiagnosticInfo: VariantType.DiagnosticInfo,
        }
        # Checking that the value is of the correct type
        if not pd.isna(self.value):
            if not isinstance(self.value, tuple(ua_class_type_to_variant_type.keys())):
                raise TypeError(
                    "Value must be one of the valid Built-In types in OPC UA"
                )
        # Checking that the type is of the correct type
        if not isinstance(self.type, VariantType):
            raise TypeError("Type must be of type VariantType")

        if self.type is VariantType.Null and not pd.isna(self.value):
            if ua_class_type_to_variant_type.get(type(self.value)) is not None:
                object.__setattr__(
                    self, "type", ua_class_type_to_variant_type.get(type(self.value))
                )
            else:
                raise ValueError(
                    "Variant type was not provided and could not be inferred from the value type"
                )

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<Variant"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        if not pd.isna(self.value):
            x += "<Value>"
            if isinstance(self.value, UABuiltIn) and hasattr(self.value, "xml_encode"):
                x += self.value.xml_encode(include_xmlns=include_xmlns)
            else:
                x += escape(str(self.value))
            x += "</Value>"
        x += "</Variant>"
        return x

    def json_encode(self, **kwargs) -> str:
        if pd.isna(self.value):
            return "null"
        if self.type is VariantType.Null:
            return "null"

        if isinstance(self.value, UABuiltIn) and hasattr(self.value, "json_encode"):
            body_json = self.value.json_encode(**kwargs)
        elif isinstance(self.value, str):
            body_json = '"' + str(self.value) + '"'
        elif isinstance(self.value, (int, float)):
            body_json = str(self.value)
        elif isinstance(self.value, bool):
            body_json = '"' + str(self.value).lower() + '"'
        else:
            raise TypeError(f"Variant value type {type(self.value)} is not supported")

        if body_json is None:
            return "null"

        json_content = "{" + '"Type":' + str(self.type.value) + ","
        json_content += '"Body":' + body_json + "}"
        return json_content


@dataclass(eq=True, frozen=True)
class UADataValue(UABuiltIn):
    pass


@dataclass(eq=True, frozen=True)
class UADecimal(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAEnumeration(UAInt32):
    string: str = ""
    name: str = ""

    def __post_init__(self):
        if not isinstance(self.string, str):
            raise TypeError("String must be a string")
        if not isinstance(self.name, str):
            raise TypeError("Name must be a string")


@dataclass(eq=True, frozen=True)
class UAArray(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAStructure(UAData):
    value: Any = pd.NA

    def xml_encode(self, include_xmlns: bool) -> str:
        if pd.isna(self.value):
            return ""
        if not pd.isna(self.value) and hasattr(self.value, "xml_encode"):
            return self.value.xml_encode(include_xmlns)
        else:
            return ""

    def json_encode(self, **kwargs) -> str:
        if pd.isna(self.value):
            return "null"
        if not pd.isna(self.value) and hasattr(self.value, "json_encode"):
            return self.value.json_encode(**kwargs)
        else:
            return "null"


@dataclass(eq=True, frozen=True)
class UAStructureOptionalField(UAData):
    pass


@dataclass(eq=True, frozen=True)
class UAExtensionObject(UABuiltIn):
    type_nodeid: UANodeId = pd.NA
    body: Union[UAByteString, UAStructure, UAXMLElement] = pd.NA
    encoding_json: int = pd.NA

    def __post_init__(self):
        if not isinstance(self.type_nodeid, UANodeId):
            raise TypeError("ExtensionObject must have a type_nodeid")
        if not isinstance(self.body, (UAByteString, UAStructure, UAXMLElement)):
            raise TypeError(
                "ExtensionObject must have a body of type UAByteString, UAStructure or UAXMLElement"
            )

        instance_map = {
            UAStructure: 0,
            UAByteString: 1,
            UAXMLElement: 2,
            0: pd.NA,
        }
        object.__setattr__(
            self, "encoding_json", instance_map.get(self.body.__class__, pd.NA)
        )

    def xml_encode(self, include_xmlns: bool) -> str:
        x = "<ExtensionObject"
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">"
        x += (
            "<TypeId>"
            + (
                self.type_nodeid.xml_encode(include_xmlns=False)
                if not pd.isna(self.type_nodeid)
                else ""
            )
            + "</TypeId>"
        )
        x += (
            "<Body>"
            + (
                self.body.xml_encode(include_xmlns=False)
                if not pd.isna(self.body)
                else ""
            )
            + "</Body>"
        )
        x += "</ExtensionObject>"
        return x

    def json_encode(self, **kwargs) -> str:
        if pd.isna(self.body) or not hasattr(self.body, "json_encode"):
            return "null"
        if self.body.json_encode(**kwargs) is None:
            return "null"

        json = ""
        json += '"TypeId":' + self.type_nodeid.json_encode() + ","

        # The body can be a ByteString, Structure or an XML Element and
        # has to have a json_encode method.
        if self.body.json_encode(**kwargs) is None:
            return "null"
        elif self.body.json_encode(**kwargs) is not None:
            json += '"Body":' + self.body.json_encode(**kwargs)
        else:
            raise TypeError(
                f"ExtensionObject body type {type(self.body)} is not supported"
            )

        # OPC UA Spec: If the Body is None, NULL, or 0 (Structure), the Encoding field shall be omitted.
        if (not pd.isna(self.encoding_json)) and (self.encoding_json != 0):
            json += ","
            json += '"Encoding":' + str(self.encoding_json)
        return "{" + json + "}"


@dataclass(eq=True, frozen=True)
class UAEUInformation(UAData):
    display_name: UALocalizedText = pd.NA
    description: UALocalizedText = pd.NA
    unit_id: int = pd.NA
    namespace_uri: str = pd.NA

    def __post_init__(self):
        if not isinstance(self.display_name, UALocalizedText) and isinstance(
            self.display_name, str
        ):
            object.__setattr__(
                self, "display_name", UALocalizedText(text=self.display_name)
            )
        elif isinstance(self.display_name, UALocalizedText) or pd.isna(
            self.display_name
        ):
            object.__setattr__(self, "display_name", self.display_name)
        else:
            raise TypeError("display_name must be of type UALocalizedText")

        if not isinstance(self.description, UALocalizedText) and isinstance(
            self.description, str
        ):
            object.__setattr__(
                self, "description", UALocalizedText(text=self.description)
            )
        elif isinstance(self.description, UALocalizedText) or pd.isna(self.description):
            object.__setattr__(self, "description", self.description)
        else:
            raise TypeError("description must be of type UALocalizedText")

        if not isinstance(self.unit_id, int):
            raise TypeError("unit_id must be of type int")
        object.__setattr__(self, "unit_id", self.unit_id)

        if not isinstance(self.namespace_uri, str):
            raise TypeError("namespace_uri must be of type str")
        object.__setattr__(self, "namespace_uri", self.namespace_uri)

    def xml_encode(self, include_xmlns: bool) -> str:
        body_contents = "<EUInformation"
        if include_xmlns:
            body_contents += ' xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"'
        body_contents += ">"
        body_contents += "<NamespaceUri>" + self.namespace_uri + "</NamespaceUri>"
        body_contents += "<UnitId>" + str(self.unit_id) + "</UnitId>"
        body_contents += "<DisplayName>"
        body_contents += (
            "<Locale>"
            + (
                self.display_name.locale
                if not pd.isna(self.display_name.locale)
                else "en"
            )
            + "</Locale>"
        )
        body_contents += (
            "<Text>"
            + (self.display_name.text if not pd.isna(self.display_name.text) else "")
            + "</Text>"
        )
        body_contents += "</DisplayName>"
        body_contents += "<Description>"
        body_contents += (
            "<Locale>"
            + (
                self.description.locale
                if not pd.isna(self.description.locale)
                else "en"
            )
            + "</Locale>"
        )
        body_contents += (
            "<Text>"
            + (self.description.text if not pd.isna(self.description.text) else "")
            + "</Text>"
        )
        body_contents += "</Description>"
        body_contents += "</EUInformation>"

        return body_contents

    def json_encode(self, **kwargs) -> Union[str, None]:
        if (
            self.display_name.json_encode(input_locale=kwargs.get("input_locale"))
            is None
            or self.description.json_encode(input_locale=kwargs.get("input_locale"))
            is None
        ):
            return None

        json_content = ""
        decoded_display_name = self.display_name.json_encode(
            input_locale=kwargs.get("input_locale", None)
        )
        json_content += (
            '{"DisplayName":' + decoded_display_name + ","
            if decoded_display_name
            else '""' + ","
        )
        decoded_description = self.description.json_encode(
            input_locale=kwargs.get("input_locale", None)
        )
        json_content += (
            '"Description":' + decoded_description + ","
            if decoded_description
            else '""' + ","
        )
        json_content += '"UnitId":' + str(self.unit_id) + ","
        json_content += '"NamespaceUri":' + json.dumps(
            self.namespace_uri, ensure_ascii=False
        )
        json_content += "}"
        return json_content


@dataclass(eq=True, frozen=True)
class UAEngineeringUnits(UAData):
    ua_eu_information: UAEUInformation

    def __init__(
        self,
        display_name: UALocalizedText,
        description: UALocalizedText,
        unit_id: int,
        namespace_uri: str,
    ):
        object.__setattr__(
            self,
            "ua_eu_information",
            UAEUInformation(
                display_name=display_name,
                description=description,
                unit_id=unit_id,
                namespace_uri=namespace_uri,
            ),
        )

    def __repr__(self):
        """
        Fixed object representation, so it can be reinstantiated with performing
        eval() on the object's representation string.
        """
        ua_eu_information_param_name = list(self.__dataclass_fields__.keys())[0]
        ua_eu_information_repr = repr(getattr(self, ua_eu_information_param_name))
        ua_eu_information = getattr(self, ua_eu_information_param_name)
        return ua_eu_information_repr.replace(
            ua_eu_information.__class__.__name__, self.__class__.__name__, 1
        )

    def xml_encode(self, include_xmlns: bool) -> str:
        ua_type_nodeid = UANodeId(0, NodeIdType.NUMERIC, "888")
        ua_extension_object = UAExtensionObject(
            type_nodeid=ua_type_nodeid,
            body=UAStructure(value=self.ua_eu_information),
        )
        return ua_extension_object.xml_encode(include_xmlns)

    def json_encode(self, **kwargs) -> str:
        ua_type_nodeid = UANodeId(0, NodeIdType.NUMERIC, "888")
        ua_extension_object = UAExtensionObject(
            type_nodeid=ua_type_nodeid,
            body=UAStructure(value=self.ua_eu_information),
        )
        return ua_extension_object.json_encode(**kwargs)


@dataclass(eq=True, frozen=True)
class UARange(UAData):
    low: float
    high: float

    def __post_init__(self):
        if self.low > self.high:
            raise ValueError("low must be less than or equal to high")
        if isinstance(self.low, int):
            object.__setattr__(self, "low", float(self.low))
        if isinstance(self.high, int):
            object.__setattr__(self, "high", float(self.high))

    def xml_encode(self, include_xmlns: bool) -> str:
        body_contents = "<Range"
        if include_xmlns:
            body_contents += ' xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"'
        body_contents += ">"
        body_contents += f"<Low>{self.low}</Low>"
        body_contents += f"<High>{self.high}</High>"
        body_contents += "</Range>"
        return body_contents

    def json_encode(self) -> str:
        json = ""
        json += '"Low":' + UADouble(self.low).json_encode() + ","
        json += '"High":' + UADouble(self.high).json_encode()
        return "{" + json + "}"


@dataclass(eq=True, frozen=True)
class UAEURange(UAData):
    ua_range: UARange

    def __init__(self, low: float, high: float):
        if not isinstance(low, (float, int)):
            raise TypeError("low must be of type float")
        if not isinstance(high, (float, int)):
            raise TypeError("high must be of type float")

        object.__setattr__(self, "ua_range", UARange(low=float(low), high=float(high)))

    def __repr__(self):
        """
        Fixed object representation, so it can be reinstantiated with performing
        eval() on the object's representation string.
        """
        ua_range_param_name = list(self.__dataclass_fields__.keys())[0]
        ua_range_repr = repr(getattr(self, ua_range_param_name))
        ua_range = getattr(self, ua_range_param_name)
        return ua_range_repr.replace(
            ua_range.__class__.__name__, self.__class__.__name__, 1
        )

    def xml_encode(self, include_xmlns: bool) -> str:
        ua_type_nodeid = UANodeId(0, NodeIdType.NUMERIC, "885")
        ua_extension_object = UAExtensionObject(
            type_nodeid=ua_type_nodeid, body=UAStructure(value=self.ua_range)
        )

        return ua_extension_object.xml_encode(include_xmlns)

    def json_encode(self) -> str:
        ua_type_nodeid = UANodeId(0, NodeIdType.NUMERIC, "885")
        ua_extension_object = UAExtensionObject(
            type_nodeid=ua_type_nodeid, body=UAStructure(value=self.ua_range)
        )
        return ua_extension_object.json_encode()


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

    def __post_init__(self):
        if not self.value:
            raise ValueError("UAListOf value must contain at least one element")
        if not isinstance(self.value, Tuple):
            raise TypeError("UAListOf value must be a Tuple")
        first_element_type = type(self.value[0])
        if any(
            not isinstance((_element := element), first_element_type)
            for element in self.value
        ):
            raise TypeError(
                f"UAListOf must contain only one type of UAData. {first_element_type} != {type(_element)}"
            )

    def xml_encode(self, include_xmlns: bool) -> str:
        encodedvalues = [v.xml_encode(include_xmlns=False) for v in self.value]
        x = "<ListOf" + self.typename + " "
        if include_xmlns:
            x += " " + UAXMLNS_ATTRIB
        x += ">" + "".join(encodedvalues) + "</ListOf" + self.typename + ">"
        return x

    def json_encode(self) -> str:
        """Extracts the values of a UAListOf object and hard codes the values within it
        in order to be able to create the proper json_encoding as it aggregates all of the
        values in a list.

        Returns:
            str: A string representing the json encoding of the UAListOf object.
        """
        try:
            str_list = [str(element.value) for element in self.value]
        except AttributeError:
            print("UAListOf json_encode error")
        ua_list_string = "[" + ",".join(str_list) + "]"

        return (
            f"""{{"Type":{VariantType[self.typename].value},"Body":{ua_list_string}}}"""
        )


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

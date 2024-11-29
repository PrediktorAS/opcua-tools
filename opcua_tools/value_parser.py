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

import base64
import copy
import functools
import re
from typing import Dict, Optional, Tuple

import lxml.etree as ET
import pandas as pd
from dateutil import parser

from opcua_tools.ua_data_types import (
    NodeIdType,
    UABoolean,
    UAByte,
    UAByteString,
    UADateTime,
    UADouble,
    UAEngineeringUnits,
    UAEURange,
    UAExtensionObject,
    UAFloat,
    UAGuid,
    UAInt16,
    UAInt32,
    UAInt64,
    UAListOf,
    UALocalizedText,
    UANodeId,
    UASByte,
    UAString,
    UAUInt16,
    UAUInt32,
    UAUInt64,
    UAXMLElement,
)

simple = {
    "Boolean",
    "SByte",
    "Byte",
    "Int16",
    "UInt16",
    "Int32",
    "UInt32",
    "Int64",
    "UInt64",
    "Float",
    "Double",
    "String",
    "DateTime",
    "Guid",
    "ByteString",
    "NodeId",
}

tagsplit = re.compile(r"({.*\})(.*)")
uaxsd = "{http://opcfoundation.org/UA/2008/02/Types.xsd}"


def parse_value(val):
    v = next(v for v in val)
    return parse_value_element(v)


def parse_value_element(v):
    tagtype = tagsplit.match(v.tag).group(2)

    if tagtype.startswith("ListOf"):
        return parse_list_value(v, tagtype)

    return parse_singular_value(v, tagtype)


def parse_list_value(val, tagtype):
    typename = re.fullmatch(r"^ListOf(.*)", tagtype).group(1)
    l = []
    for v in val:
        l.append(parse_value_element(v))
    return UAListOf(value=tuple(l), typename=typename)


def parse_singular_value(val, tagtype):
    if tagtype in simple:
        if val.text is not None:
            stripped = val.text.strip()
        else:
            stripped = None
        if tagtype == "SByte":
            if stripped:
                return UASByte(value=int(stripped))

            return UASByte(value=None)

        elif tagtype == "Byte":
            if stripped:
                return UAByte(value=int(stripped))

            return UAByte(value=None)

        elif tagtype == "Int16":
            if stripped:
                return UAInt16(value=int(stripped))

            return UAInt16(value=None)

        elif tagtype == "UInt16":
            if stripped:
                return UAUInt16(value=int(stripped))

            return UAUInt16(value=None)

        elif tagtype == "Int32":
            if stripped:
                return UAInt32(value=int(stripped))

            return UAInt32(value=None)

        elif tagtype == "UInt32":
            if stripped:
                return UAUInt32(value=int(stripped))

            return UAUInt32(value=None)

        elif tagtype == "Int64":
            if stripped:
                return UAInt64(value=int(stripped))

            return UAInt64(value=None)

        elif tagtype == "UInt64":
            if stripped:
                return UAUInt64(value=int(stripped))

            return UAUInt64(value=None)

        elif tagtype == "Float":
            if stripped:
                return UAFloat(value=float(stripped))

            return UAFloat(value=None)

        elif tagtype == "Double":
            if stripped:
                return UADouble(value=float(stripped))

            return UADouble(value=None)

        elif tagtype == "String":
            if stripped is not None:
                return UAString(value=stripped)

            return UAString(value=None)

        elif tagtype == "DateTime":
            parsed = parser.parse(stripped)
            return UADateTime(value=parsed)

        elif tagtype == "Boolean":
            if stripped == "":
                return UABoolean(value=None)

            return parse_boolean(stripped)

        elif tagtype == "ByteString":
            if stripped is not None:
                return UAByteString(value=base64.b64decode(stripped))

            return UAByteString(value=None)

        elif tagtype == "Guid":
            if stripped is not None:
                return UAGuid(value=stripped)

            return UAGuid(value=None)

        elif tagtype == "NodeId":
            if val.text is not None:
                return parse_nodeid(val.text)

            return None

    elif tagtype == "TypeId":
        ident = val.find(uaxsd + "Identifier")
        return parse_nodeid(ident.text)

    elif tagtype == "LocalizedText":
        return parse_localized_text(val)

    elif tagtype == "ExtensionObject":
        typeid = val.find(uaxsd + "TypeId")
        if typeid is None:
            parsed_typeid = None
        else:
            parsed_typeid = parse_value_element(typeid)

        body = val.find(uaxsd + "Body")

        if parsed_typeid is not None:
            if (
                parsed_typeid.namespace == 0
                and parsed_typeid.nodeid_type == NodeIdType.NUMERIC
                and parsed_typeid.value == "888"
            ):
                return parse_engineering_units(body)
            if (
                parsed_typeid.namespace == 0
                and parsed_typeid.nodeid_type == NodeIdType.NUMERIC
                and parsed_typeid.value == "885"
            ):
                return parse_eu_range(body)

        if body is not None and len(body) > 0:
            nextbody = next(n for n in body)
            if nextbody is None:
                parsednextbody = None
            else:
                parsednextbody = parse_value_element(nextbody)
        else:
            parsednextbody = None

        if parsednextbody is not None and parsed_typeid is not None:
            return UAExtensionObject(type_nodeid=parsed_typeid, body=parsednextbody)
        else:
            return None

    else:
        # Need to copy element, cleanup_namespaces only works if a copy is made
        val_copy = copy.copy(val)
        # Remove unused xml namespaces
        ET.cleanup_namespaces(val_copy)

        return UAXMLElement(value=ET.tostring(val_copy).decode("utf-8"))

    raise NotImplementedError(tagtype)


@functools.cache
def cached_parse_nodeid(
    nodeidstr: str,
) -> Tuple[int, NodeIdType, str]:
    if "ns" in nodeidstr:
        nodeidstr_split = nodeidstr.split(";")
        ns = int(nodeidstr_split[0].split("=")[1])
        nodeid_type, value = nodeidstr_split[1].split("=", maxsplit=1)
        nodeid_type = NodeIdType(nodeid_type)
        return ns, nodeid_type, str(value)

    nodeidstr_split = nodeidstr.split("=", maxsplit=1)
    if len(nodeidstr_split) == 2:
        nodeid_type = nodeidstr_split[0]
        value = nodeidstr_split[1]
        return 0, NodeIdType(nodeid_type), str(value)

    raise ValueError("Could not parse {nodeid}".format(nodeid=nodeidstr))


def parse_nodeid(
    nodeidstr: str,
    namespace_map: Optional[Dict[int, int]] = None,
    alias_map: Optional[Dict[str, UANodeId]] = None,
):
    if alias_map is not None and nodeidstr in alias_map:
        return alias_map[nodeidstr]

    if namespace_map:
        ns, nodeid_type, value = cached_parse_nodeid(nodeidstr)
        ns = namespace_map[ns]

    else:
        ns, nodeid_type, value = cached_parse_nodeid(nodeidstr)

    return UANodeId(ns, nodeid_type, value)


def parse_localized_text(el):
    txt = el.find(uaxsd + "Text")
    if txt is None:
        text = pd.NA
    else:
        text = txt.text

    loc = el.find(uaxsd + "Locale")
    if loc is None:
        locale = pd.NA
    elif loc.text is None:
        locale = pd.NA
    elif type(loc.text) == str:
        loc_text_str = loc.text.strip()
        if loc_text_str == "":
            locale = pd.NA
        else:
            locale = loc.text
    else:
        raise ValueError("Unexpected type for localized text locale")

    return UALocalizedText(text=text, locale=locale)


def parse_engineering_units(el):
    if el is not None:
        euinfo = el.find(uaxsd + "EUInformation")
        if euinfo is not None:
            namespace_uri_tag = euinfo.find(uaxsd + "NamespaceUri")
            if namespace_uri_tag.text is not None:
                namespace_uri = namespace_uri_tag.text.rstrip()
                unit_id_tag = euinfo.find(uaxsd + "UnitId")
                unit_id = int(unit_id_tag.text.strip())

                display_name_tag = euinfo.find(uaxsd + "DisplayName")
                display_name = parse_localized_text(display_name_tag)
                description_tag = euinfo.find(uaxsd + "Description")
                description = parse_localized_text(description_tag)
                return UAEngineeringUnits(
                    display_name=display_name,
                    description=description,
                    unit_id=unit_id,
                    namespace_uri=namespace_uri,
                )


def parse_eu_range(el):
    if el is not None:
        range_tag = el.find(uaxsd + "Range")
        if range_tag is not None:
            low_tag = range_tag.find(uaxsd + "Low")
            low = float(low_tag.text.strip())
            high_tag = range_tag.find(uaxsd + "High")
            high = float(high_tag.text.strip())
            return UAEURange(
                low=low,
                high=high,
            )


def parse_boolean(string):
    if string is not None:
        if string in ["true", "True"]:
            return UABoolean(value=True)
        else:
            return UABoolean(value=False)

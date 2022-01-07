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


from .ua_graph import UAGraph
from typing import Tuple
from .ua_data_types import (
    UAEnumeration,
    UAInt32,
    UAListOf,
    UnparsedUAExtensionObject,
    UALocalizedText,
)

import xmltodict
import pandas as pd
import logging


logger = logging.getLogger(__name__)
cl = logging.StreamHandler()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
cl.setFormatter(formatter)
logger.addHandler(cl)


def get_enum_type_definition(ua_graph: UAGraph, data_type_id: int):
    """Given a UAGraph object and a internal id of an enum type,
    the definition of the enumeration will be produced. The form
    of the definition may vary based on the enumeration.

    Args:
       ua_graph (UAGraph): UAGraph where the enum defintion is found
       data_type_id (int): The internal id for data type enum

    Return:
       The content of the 'Values' column in the node definition

    """

    enum_type_row = ua_graph.nodes[ua_graph.nodes["id"] == data_type_id]
    enum_type_id = enum_type_row["id"].values[0]

    # The enum type points to the enum definition via HasProperty ReferenceType.
    # The enum type does not contain the enum definition itself, it points to
    # an EnumStrings or EnumValues
    enum_neighbors = ua_graph._get_neighboring_nodes_by_id(enum_type_id, "outgoing")
    # Ensuring we are getting the HasProperty reference
    enum_neighbors_has_property = enum_neighbors[
        enum_neighbors["ReferenceType"] == "HasProperty"
    ]

    # Getting the node which actually defines the enum
    enum_definition_id = enum_neighbors_has_property["Trg"].values[0]
    enum_definition_node = ua_graph.nodes[ua_graph.nodes["id"] == enum_definition_id]
    enum_ua_list_of = enum_definition_node["Value"].values[0]

    return enum_ua_list_of


def create_enum_dict_from_enum_tuples(enum_tuple: Tuple) -> dict[int, str]:
    """Gets the tuple contents of enums and will attempt to parse the tuple
    to create and return a dictionary of the enumeration definition.

    Args:
       enum_tuple (Tuple): Tuple containing enumeration definition

    Return:
       A dictionary which defines the enumeration

    """

    # The enum definition can be stored in different ways. The two versions observed
    # is as an unparsed UAExtentionObject in xml or as UALocalizedText.
    enum_dict = dict()
    for index, content in enumerate(enum_tuple):
        if isinstance(content, UnparsedUAExtensionObject):
            ua_structure = content.body
            xml_string = ua_structure.xmlstring
            xml_dict = xmltodict.parse(xml_string)

            value = int(xml_dict["EnumValueType"]["Value"])
            text = xml_dict["EnumValueType"]["DisplayName"]["Text"]
            enum_dict[value] = text
        elif isinstance(content, UALocalizedText):
            value = index
            text = content.text
            enum_dict[value] = text
        else:
            raise ValueError(f"The enum content was not supported: {content}")

    if not enum_dict:
        raise ValueError("The enum dict was not correctly iterated over")

    return enum_dict


def instantiate_enum_class(row: pd.DataFrame, ua_graph: UAGraph):
    """For a single row in the nodes dataframe, which represents an enum value,
    it will produce an UAEnumeration class based on; the Int provided in the
    row, the name of the enumeration which is references by the datatype, and
    the corresponding string value found in the enums definition.

    Args:
       ua_graph (UAGraph): UAGraph object to transform

    Return:
       The modified UAGraph with Enumeration classes

    """

    # In some cases the Value is 'None' for some enums and should do
    # nothing in this case
    if row["Value"] == None:
        return None

    # Extracting the actual numeric value as UAInt32 class
    if isinstance(row["Value"], UAInt32):
        ua_int = row["Value"].value
    elif isinstance(row["Value"], UAListOf):
        ua_int = row["Value"].value[0].value
    else:
        raise ValueError(f"row['Value']: {row['Value']} has not been handled properly")

    # Find the enumeration type name for the variable
    data_type_id = row["DataType"]
    data_type_name = ua_graph._get_browsename_from_id(data_type_id)

    # Getting the enum type row value
    enum_ua_list_of = get_enum_type_definition(ua_graph, data_type_id)
    enum_tuple = enum_ua_list_of.value
    enum_dict = create_enum_dict_from_enum_tuples(enum_tuple)
    string = enum_dict[ua_int]

    enum_class = UAEnumeration(value=ua_int, string=string, name=data_type_name)

    return enum_class


def transform_ints_to_enums(ua_graph: UAGraph):
    """Transforms the integer values in the Value column
    for the Enum data types, to the Enumeration python class. It modifies
    the input UAGraph directly

    Args:
       ua_graph (UAGraph): UAGraph object to transform

    """

    # Extracting nodes for readability
    nodes = ua_graph.nodes.copy()

    # Have to find all children of the Enumeration class
    enumeration_id = ua_graph.data_type_by_browsename("Enumeration")
    enumeration_children = ua_graph._get_neighboring_nodes_by_id(
        enumeration_id, "outgoing"
    )

    # Extracting UAVariables which datatypes are Enumeration subtypes
    enum_data_type_ids = enumeration_children["Trg"]
    enum_nodes = nodes.loc[nodes["DataType"].isin(enum_data_type_ids)]
    enum_nodes = enum_nodes[enum_nodes["NodeClass"] == "UAVariable"]

    enum_nodes["Value"] = enum_nodes.apply(
        lambda x: instantiate_enum_class(x, ua_graph), axis=1
    )

    # Putting the modified nodes back into the nodes dataframe by index
    nodes.loc[enum_nodes.index, :] = enum_nodes[:]

    ua_graph.nodes = nodes

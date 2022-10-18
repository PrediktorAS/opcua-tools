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


from opcua_tools.ua_graph import UAGraph
from typing import Dict
from opcua_tools.ua_data_types import (
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
logger.addHandler(logging.NullHandler())


def create_enum_dict_from_enum_tuples(row: pd.DataFrame) -> Dict[int, str]:
    """Gets the row for the enum node and will attempt to parse the tuple in the
    'Value' column to create and return a dictionary of the enumeration definition.

    Args:
       row (pd.DataFrame): A row of the enumeration which contains a definition with a tuple to parse

    Return:
       A dictionary which defines the enumeration

    """

    # The enum definition can be stored in different ways. The two versions observed
    # is as an unparsed UAExtentionObject in xml or as UALocalizedText.
    enum_tuple = row["Value"]
    enum_dict = dict()
    for index, content in enumerate(enum_tuple):
        if isinstance(content, UnparsedUAExtensionObject):
            ua_structure = content.body
            xml_string = ua_structure.xmlstring
            xml_dict = xmltodict.parse(xml_string)

            # This notation and searching is to ignore xmlns handling
            enum_value_dict = [
                val for key, val in xml_dict.items() if "EnumValueType" in key
            ]
            value = [val for key, val in enum_value_dict[0].items() if "Value" in key][
                0
            ]
            if value.isdigit():
                value = int(value)
            enum_value_dict = [
                val for key, val in xml_dict.items() if "EnumValueType" in key
            ][0]
            display_name_dict = [
                val for key, val in enum_value_dict.items() if "DisplayName" in key
            ][0]
            text = [val for key, val in display_name_dict.items() if "Text" in key][0]
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


def instantiate_enum_class(row: pd.DataFrame) -> UAEnumeration:
    """For a single row from a modified nodes dataframe, which represents an enum value,
    it will produce an UAEnumeration class based on; the Int provided in the
    row, the name of the enumeration which is references by the datatype, and
    the corresponding string value found in the enums definition.

    Args:
       row (pd.DataFrame): The row from nodes with additional 'EnumDict' and 'EnumName' cols.

    Return:
       UAEnumeration class created from the row.

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
    string = row["EnumDict"][ua_int]
    data_type_name = row["EnumName"]

    enum_class = UAEnumeration(value=ua_int, string=string, name=data_type_name)

    return enum_class


def create_enum_definition_table(
    ua_graph: UAGraph, enum_data_types: pd.Series
) -> pd.DataFrame:
    """This function will create an pd.DataFrame containing the id of the DataType which
    the UAVariable for an enumeration class has, the BrowseName of the enumeration class,
    and the actual enumeration definition for that class.

    Args:
       ua_graph (UAGraph): The complete UAGraph with necessary definitions.
       enum_data_types (pd.Series): The column of DataTypes which are Enumeration definitions

    Return:
       pd.DataFrame containing the enumeration definition tables.

    """
    # Subsetting the 'nodes' table to the subset of datatypes
    enum_table = ua_graph.nodes[ua_graph.nodes["id"].isin(enum_data_types)]
    enum_table = enum_table[["id", "BrowseName"]]

    # Getting the references table pointing from the nodes in enum_table
    # via a HasProperty definition to the actual defintion in the node
    enum_references = ua_graph.references[
        ua_graph.references["Src"].isin(enum_data_types)
    ]
    has_property_id = ua_graph.reference_type_by_browsename("HasProperty")
    enum_references = enum_references[
        enum_references["ReferenceType"] == has_property_id
    ]
    enum_references = enum_references.drop(["ReferenceType"], axis=1)

    # Joining the enum_references and enum_table
    enum_table = enum_table.set_index("id", drop=False)
    enum_references = enum_references.set_index("Src", drop=True)
    enum_table = enum_table.join(enum_references, how="left")

    # Joining the enum_table's 'Trg' column to nodes to get the definition
    nodes_subset = ua_graph.nodes[["id", "Value"]].set_index("id")
    enum_table = enum_table.set_index("Trg", drop=True)
    enum_table = enum_table.join(nodes_subset, how="left")

    enum_table["Value"] = enum_table["Value"].apply(lambda row: row.value)
    enum_table["EnumDict"] = enum_table.apply(
        lambda row: create_enum_dict_from_enum_tuples(row), axis=1
    )
    enum_table = enum_table.drop(["Value"], axis=1)

    enum_table = enum_table.rename(columns={"BrowseName": "EnumName"})

    return enum_table


def transform_ints_to_enums(ua_graph: UAGraph):
    """Transforms the integer values in the Value column
    for the Enum data types, to the Enumeration python class. It modifies
    the input UAGraph directly

    Args:
       ua_graph (UAGraph): UAGraph object to transform

    """

    # Extracting nodes for readability
    nodes = ua_graph.nodes.copy()

    # Have to first if the are any Enumeration browsenames in nodes dataframe
    if not (nodes["BrowseName"] == "Enumeration").any():
        return

    # Have to find all children of the Enumeration class
    enumeration_id = ua_graph.data_type_by_browsename("Enumeration")
    enumeration_children = ua_graph.get_neighboring_nodes_by_id(
        enumeration_id, "outgoing"
    )

    # Extracting UAVariables which datatypes are Enumeration subtypes
    enum_data_type_ids = enumeration_children["Trg"]
    enum_nodes = nodes.loc[nodes["DataType"].isin(enum_data_type_ids)]
    enum_nodes = enum_nodes[enum_nodes["NodeClass"] == "UAVariable"]

    logger.info(f"The size of enum_nodes is {enum_nodes.shape}")
    enum_data_types = enum_nodes["DataType"]
    enum_def_table = create_enum_definition_table(ua_graph, enum_data_types)

    # Have to join the enum_definition_table to enum_nodes table
    enum_def_table = enum_def_table.set_index("id", drop=True)
    enum_nodes["DataType"] = enum_nodes["DataType"].astype(str).astype(int)
    enum_nodes = enum_nodes.set_index("DataType", drop=False)
    enum_nodes = enum_nodes.join(enum_def_table, how="left")

    # Apply function to create UAEnumeration in Values column
    enum_nodes["Value"] = enum_nodes.apply(
        lambda row: instantiate_enum_class(row), axis=1
    )
    enum_nodes = enum_nodes.set_index("id", drop=False)
    enum_nodes = enum_nodes.drop(["EnumName", "EnumDict"], axis=1)

    logger.info("Finished working through the enum_nodes")
    # Putting the modified nodes back into the nodes dataframe by index
    nodes.loc[enum_nodes.index, :] = enum_nodes[:]

    ua_graph.nodes = nodes
    logger.info("Finished transforming the integers to enums")

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

import os
from typing import Optional, Union, List
import time
from xml.sax.saxutils import escape
import lxml.etree as ET
from datetime import datetime
import pytz
import logging
import pandas as pd
import numpy as np
from io import StringIO
from opcua_tools.ua_data_types import UANodeId, NodeIdType

PATH_HERE = os.path.dirname(__file__)


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


simplevariants = {
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
}


def create_header_xml(
    namespaces,
    serialize_namespace,
    xmlns_dict: Optional[dict] = None,
    last_modified: Optional[datetime] = None,
    publication_date: Optional[datetime] = None,
):

    if not xmlns_dict:
        xmlns_dict = {
            "xsd": "http://www.w3.org/2001/XMLSchema",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            None: "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd",
        }

    if not last_modified:
        last_modified = datetime.now(tz=pytz.UTC)

    if not publication_date:
        publication_date = datetime.now(tz=pytz.UTC)

    prefixes = ""
    for key in xmlns_dict:
        prefix = "xmlns"
        if key:
            prefix += ":{}".format(key)
        prefixes += ' {}="{}"'.format(prefix, xmlns_dict[key])

    namespaceheader = ""
    if len(namespaces) > 1:
        namespaceheader += "<NamespaceUris>\n"
        for i, n in enumerate(namespaces):
            if i < 1:
                continue

            namespaceheader += "<Uri>{}</Uri>\n".format(n)
        namespaceheader += "</NamespaceUris>\n"

    return """<?xml version="1.0" encoding="utf-8"?>
<UANodeSet LastModified="{}" {}>
{}
<Models>
    <Model ModelUri="{}" PublicationDate="{}" Version="1.0.0"></Model>
</Models>
<Aliases></Aliases>
""".format(
        last_modified.isoformat(),
        prefixes,
        namespaceheader,
        namespaces[serialize_namespace],
        publication_date.isoformat(),
    )


def generate_references_xml(nodes, references):
    """
    :param nodes:
    :param references:
    :return:
    """

    # references = references.reset_index()
    nodes["target_same_ns"] = True
    references = references.set_index("Trg").join(
        nodes.set_index("NodeId")[["target_same_ns"]], how="left"
    )
    references = references.reset_index().rename(columns={"index": "Trg"})
    nodes.drop(columns="target_same_ns", inplace=True)
    references["target_same_ns"] = ~references["target_same_ns"].isna()

    # Default code references on target node
    references["NodeId"] = references["Trg"]

    # References where target is not in same namespace are encoded on source
    references.loc[~references["target_same_ns"], "NodeId"] = references.loc[
        ~references["target_same_ns"], "Src"
    ]

    # Outgoing reference when target is not in same nodeset
    references.loc[~references["target_same_ns"], "xml"] = (
        '<Reference ReferenceType="'
        + references.loc[~references["target_same_ns"], "ReferenceType"]
        + '">'
        + references.loc[~references["target_same_ns"], "Trg"]
        + "</Reference>"
    )

    # Incoming reference only when target is in same nodeset to be generated
    references.loc[references["target_same_ns"], "xml"] = (
        '<Reference ReferenceType="'
        + references.loc[references["target_same_ns"], "ReferenceType"]
        + '"  IsForward="false">'
        + references.loc[references["target_same_ns"], "Src"]
        + "</Reference>"
    )

    references = references.drop(columns=["target_same_ns"])
    return references


def encode_values(nodes):
    is_variable = nodes["NodeClass"] == "UAVariable"
    if "Value" in nodes.columns.values:
        has_value = ~nodes["Value"].isna()
        should_encode = is_variable & has_value
        nodes.loc[should_encode, "EncodedValue"] = nodes.loc[
            should_encode, "Value"
        ].map(lambda x: x.xml_encode(include_xmlns=True))
    else:
        nodes["EncodedValue"] = np.nan


def generate_nodes_xml(
    nodes: pd.DataFrame, references: pd.DataFrame, lookup_df: pd.DataFrame
):
    assert (
        nodes["BrowseNameNamespace"].isna().sum() == 0
    ), "Should not have missing BrowseNameNamespaces"

    replacer = lambda x: x.map(escape)
    nodes["DisplayName"] = replacer(nodes["DisplayName"])
    nodes["BrowseName"] = replacer(nodes["BrowseName"])
    nodes["Description"] = replacer(nodes["Description"])
    nodes["NodeId"] = replacer(nodes["NodeId"].map(str))

    nodes = denormalize_nodes_nodeids(nodes, lookup_df=lookup_df)
    references = denormalize_references_nodeids(references, lookup_df=lookup_df)

    references["Src"] = replacer(references["Src"].map(str))
    references["Trg"] = replacer(references["Trg"].map(str))
    references["ReferenceType"] = replacer(references["ReferenceType"].map(str))

    nodes = nodes.copy()

    encode_values(nodes)
    encode_definitions(nodes)
    nodes["nodexml"] = "<" + nodes["NodeClass"] + ' NodeId="' + nodes["NodeId"] + '"'
    if ["SymbolicName"] in nodes.columns.values:
        hasSymbolicName = ~nodes["SymbolicName"].isna()
        nodes.loc[hasSymbolicName, "nodexml"] = (
            nodes.loc[hasSymbolicName, "nodexml"]
            + ' SymbolicName="'
            + nodes.loc[hasSymbolicName, "SymbolicName"]
            + '" '
        )
    nodes["nodexml"] = (
        nodes["nodexml"]
        + ' BrowseName="'
        + nodes["BrowseNameNamespace"].astype(str)
        + ":"
        + nodes["BrowseName"]
        + '" '
    )
    for a in [
        "DataType",
        "ValueRank",
        "AccessLevel",
        "UserAccessLevel",
        "IsAbstract",
        "Symmetric",
        "ParentNodeId",
        "ArrayDimensions",
        "MinimumSamplingInterval",
        "MethodDeclarationId",
        "EventNotifier",
        "Historizing",
    ]:
        if a in nodes.columns.values:
            notna = ~nodes[a].isna()
            haslen = nodes[a].astype(str).str.len() > 0
            if a in ("IsAbstract", "Symmetric", "Historizing"):
                use_value = nodes.loc[notna & haslen, a].astype(str).str.lower()
            else:
                use_value = nodes.loc[notna & haslen, a].astype(str)

            nodes.loc[notna & haslen, "nodexml"] = (
                nodes.loc[notna & haslen, "nodexml"] + a + '="' + use_value + '" '
            )

    nodes["nodexml"] = nodes["nodexml"] + ">"
    nodes["nodexml"] = (
        nodes["nodexml"] + "<DisplayName>" + nodes["DisplayName"] + "</DisplayName>"
    )
    has_description = ~nodes["Description"].isna()
    nodes.loc[has_description, "nodexml"] = (
        nodes.loc[has_description, "nodexml"]
        + "<Description>"
        + nodes.loc[has_description, "Description"]
        + "</Description>"
    )

    new_references = generate_references_xml(nodes, references).reset_index()
    nodes_tojoin = nodes.set_index("NodeId").join(
        new_references.set_index("NodeId")[["xml"]]
    )

    nodes_tojoin["xml"] = nodes_tojoin["xml"].fillna("")
    nodes_tojoin = (
        nodes_tojoin.reset_index()
        .groupby("NodeId")
        .agg({"xml": lambda x: "".join(x.values)})[["xml"]]
    )
    nodes = nodes.set_index("NodeId").join(nodes_tojoin).reset_index()
    nodes["nodexml"] = (
        nodes["nodexml"] + "<References>" + nodes["xml"].fillna("") + "</References>"
    )
    has_encoded_value = ~nodes["EncodedValue"].isna()
    nodes.loc[has_encoded_value, "nodexml"] = (
        nodes.loc[has_encoded_value, "nodexml"]
        + "<Value>"
        + nodes.loc[has_encoded_value, "EncodedValue"]
        + "</Value>"
    )
    if "Definition" in nodes.columns.values:
        has_encoded_definition = ~nodes["EncodedDefinition"].isna()
        nodes.loc[has_encoded_definition, "nodexml"] = (
            nodes.loc[has_encoded_definition, "nodexml"]
            + nodes.loc[has_encoded_definition, "EncodedDefinition"]
        )

    nodes["nodexml"] = nodes["nodexml"] + "</" + nodes["NodeClass"] + ">"
    return nodes["nodexml"].astype(str)


def encode_definitions(nodes: pd.DataFrame):
    if "Definition" in nodes.columns.values:
        has_definition = ~nodes["Definition"].isna()
        nodes.loc[has_definition, "EncodedDefinition"] = nodes.loc[
            has_definition, "Definition"
        ].map(lambda x: x.xml_encode(include_xmlns=False))


def create_nodeset2_file(
    nodes: pd.DataFrame,
    references: pd.DataFrame,
    namespaces: List[str],
    serialize_namespace: int,
    filename_or_stringio: Union[str, StringIO] = "nodeset2.xml",
    xmlns_dict=None,
    last_modified: Optional[datetime] = None,
    publication_date: Optional[datetime] = None,
):
    nodes["ns"] = nodes["NodeId"].map(lambda x: x.namespace)
    namespaces_in_use = find_namespaces_in_use(
        nodes=nodes, references=references, namespace_index=serialize_namespace
    )
    namespaces_in_use.sort()
    nodes = nodes[nodes["ns"].map(lambda x: x in (namespaces_in_use))].copy()
    serialize_namespace_uri = namespaces[serialize_namespace]
    original_namespaces = namespaces
    namespaces = [namespaces[i] for i in namespaces_in_use]
    serialize_namespace = namespaces.index(serialize_namespace_uri)
    reindex_nodeids_browsenames(nodes, original_namespaces, namespaces)
    nodes["ns"] = nodes["NodeId"].map(lambda x: x.namespace)
    lookup_df = create_lookup_df(nodes)

    header = create_header_xml(
        namespaces,
        serialize_namespace,
        xmlns_dict=xmlns_dict,
        last_modified=last_modified,
        publication_date=publication_date,
    )
    start_time = time.time()
    logger.info("Creating nodeset2xml-node-string")

    nodes = nodes[nodes["ns"] == serialize_namespace].copy()
    # References restrict themselves

    nodes_df = generate_nodes_xml(nodes, references, lookup_df)
    end_time = time.time()
    logger.info(f"Creating nodeset2xml-string took {str(end_time - start_time)}")
    logger.info("Writing nodeset2xml")
    start_time = time.time()

    outstr = header + "\n".join(nodes_df.values) + "\n" + "</UANodeSet>"

    if type(filename_or_stringio) == str:
        with open(filename_or_stringio, "w", encoding="utf-8") as f:
            f.write(outstr)
    else:
        filename_or_stringio.write(outstr)
    end_time = time.time()
    logger.info(f"Writing nodeset2xml-file took: {str(end_time - start_time)}")


def reindex_nodeids_browsenames(
    nodes: pd.DataFrame, original_namespaces: List[str], namespaces: List[str]
):
    namespace_map = {original_namespaces.index(n): i for i, n in enumerate(namespaces)}
    nodes["NodeId"] = nodes["NodeId"].map(
        lambda x: copy_nodeid_with_new_namespace(x, namespace_map[x.namespace])
    )
    nodes["BrowseNameNamespace"] = (
        nodes["BrowseNameNamespace"].map(namespace_map).astype(pd.Int32Dtype())
    )


def copy_nodeid_with_new_namespace(uanodeid: UANodeId, new_ns: int):
    return UANodeId(
        namespace=new_ns, value=uanodeid.value, nodeid_type=uanodeid.nodeid_type
    )


def copy_browsename_with_new_namespace(uanodeid: UANodeId, new_ns: int):
    return UANodeId(
        namespace=new_ns, value=uanodeid.value, nodeid_type=uanodeid.nodeid_type
    )


def validate_nodeset2_file(filename: str):
    start_time = time.time()
    tree = ET.parse(PATH_HERE + "/static/UANodeSet.xsd")
    schema = ET.XMLSchema(tree)
    parser = ET.XMLParser(schema=schema)
    try:
        ET.parse(filename, parser)
        logger.info("XML validated by nodeset2 xsd")
    except Exception as e:
        logger.info("XML is invalid according to nodeset2 xsd")
        logger.info("Error occured:")
        logger.info(e)
    end_time = time.time()
    logger.info(f"Validating nodeset2xml-file took: {str(end_time - start_time)}")


def create_lookup_df(nodes):
    return (
        nodes[["id", "NodeId"]]
        .rename(columns={"NodeId": "uniques"})
        .set_index("id", drop=True)
    )


def denormalize_nodes_nodeids(nodes, lookup_df):
    nodecols = ["ParentNodeId", "DataType", "MethodDeclarationId"]

    for c in nodecols:
        if c in nodes.columns.values:
            uniques = lookup_df.rename(columns={"uniques": c}, errors="raise")
            nodes = nodes.set_index(c).join(uniques).reset_index(drop=True)
    return nodes


def denormalize_references_nodeids(references, lookup_df):
    refcols = ["Src", "Trg", "ReferenceType"]
    for c in refcols:
        uniques = lookup_df.rename(columns={"uniques": c}, errors="raise")
        references = references.set_index(c).join(uniques).reset_index(drop=True)
    return references


def find_namespaces_in_use(nodes, references, namespace_index):
    """Find the namespaces which are in use and the BrowseNameNamespaces
    which are used but already in the list"""
    cs = ["DataType", "ParentNodeId", "MethodDeclarationId"]
    other_nodes = []
    for c in cs:
        if c in nodes.columns.values:
            other_nodes.append(c)
    ids_in_ns = nodes.loc[nodes["ns"] == namespace_index, ["id"] + other_nodes].copy()
    ids_in_ns = ids_in_ns.set_index("id", drop=False)

    references_source_in_ns = references.set_index("Src")
    references_source_in_ns = references_source_in_ns[
        references_source_in_ns.index.isin(ids_in_ns.index)
    ]

    all_ids_set = set(ids_in_ns["id"])

    all_ids_set = all_ids_set.union(set(references_source_in_ns["Trg"]))
    all_ids_set = all_ids_set.union(set(references_source_in_ns["ReferenceType"]))

    references_target_in_ns = references.set_index("Trg")
    references_target_in_ns = references_target_in_ns[
        references_target_in_ns.index.isin(ids_in_ns.index)
    ]

    all_ids_set = all_ids_set.union(set(references_target_in_ns["Src"]))
    all_ids_set = all_ids_set.union(set(references_target_in_ns["ReferenceType"]))

    for c in other_nodes:
        if c in nodes.columns.values:
            all_ids_set = all_ids_set.union(ids_in_ns[c].dropna())

    output_nodes = pd.DataFrame({"id": list(all_ids_set)}).set_index("id")
    nodes = nodes.set_index("id")
    namespaces_in_use = list(
        nodes.loc[nodes.index.isin(output_nodes.index), "ns"].dropna().unique()
    )
    # Adding the BrowseNameNamespaces which are not already in the namespace list
    browsename_namespaces = list(
        nodes.loc[nodes["ns"] == namespace_index, "BrowseNameNamespace"].unique()
    )
    namespaces_in_use = list(set(namespaces_in_use + browsename_namespaces))

    return namespaces_in_use

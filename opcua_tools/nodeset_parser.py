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
import re
import logging
from typing import List, Dict, Any, Optional, Union
from opcua_tools.value_parser import parse_value, parse_nodeid
from opcua_tools.ua_data_types import UANodeId

import lxml.etree as ET
import pandas as pd
import logging
from io import BytesIO


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

tagsplit = re.compile(r"({.*\})(.*)")


def findrefs(
    elem, uaxsd, namespace_map: Dict[int, int], alias_map: Dict[str, UANodeId]
):
    return [
        (
            parse_nodeid(r.text.rstrip(), namespace_map, alias_map),
            fix_ref_attrib(r, namespace_map, alias_map),
        )
        for refs in elem.findall(uaxsd + "References")
        for r in refs.findall(uaxsd + "Reference")
    ]


def findval(elem, uaxsd):
    val = elem.find(uaxsd + "Value")
    if val is None:
        return None

    if len(val) < 1:
        return None

    return parse_value(val)


def finddisplayname(elem, uaxsd):
    val = elem.find(uaxsd + "DisplayName")
    if val is None:
        return ""

    if val.text is None:
        return ""

    return val.text.rstrip()


def finddescription(elem, uaxsd):
    val = elem.find(uaxsd + "Description")
    if val is None:
        return ""

    if val.text is None:
        return ""

    return val.text.rstrip()


def parse_node_attrib(
    elem: ET.ElementBase, namespace_map: Dict[int, int], alias_map: Dict[str, UANodeId]
) -> Dict[str, str]:
    """
    Parses the xml element for the node and maps NodeId, DataType (if any), ParentNodeID(if any)
    in the Attribute Dictionary.

    Parameters:
    elem (XML element): the XML element to parse
    namespace_map (Dict[str,str]): The dictionary used for mapping of ns index

    Returns:
    Dict[str,str] with attributes according to NodeClass in xml element
    """
    attrib = dict(elem.attrib)
    # Map NodeId
    attrib["NodeId"] = parse_nodeid(attrib["NodeId"], namespace_map, alias_map)
    if "DataType" in attrib:
        attrib["DataType"] = parse_nodeid(attrib["DataType"], namespace_map, alias_map)
    if "ParentNodeId" in attrib:
        attrib["ParentNodeId"] = parse_nodeid(
            attrib["ParentNodeId"], namespace_map, alias_map
        )
    if "MethodDeclarationId" in attrib:
        attrib["MethodDeclarationId"] = parse_nodeid(
            attrib["MethodDeclarationId"], namespace_map, alias_map
        )

    return attrib


def fix_ref_attrib(
    elem: ET.ElementBase, namespace_map: Dict[int, int], alias_map: Dict[str, UANodeId]
) -> Dict[str, str]:
    """
    Parses the xml element for the reference and maps ReferenceType  in the attribute Dictionary.

    Parameters:
    elem (XML element): the XML element to parse
    namespace_map (Dict[str,str]): The dictionary used for mapping of ns index

    Returns:
    Dict[str,str] with attributes according to the reference xml element
    """
    attrib = dict(elem.attrib)
    attrib["ReferenceType"] = parse_nodeid(
        attrib["ReferenceType"], namespace_map, alias_map=alias_map
    )
    return attrib


def process_elem_batch(
    elems: List[ET.ElementBase],
    uaxsd: str,
    namespace_map: Dict[int, int],
    alias_map: Dict[str, UANodeId],
) -> pd.DataFrame:
    """
    Creates a Pandas DataFrame with node and reference info based on the provided XML element list

    Parameters:

    Returns:
    Pandas DataFrame with columns:[Tag,Attrib,DisplayName, Description, References, ValueTmp]

    """
    df = pd.DataFrame({"elem": elems})
    df["Tag"] = df["elem"].map(lambda x: x.tag).str.replace(uaxsd, "", regex=True)
    df["Attrib"] = df["elem"].map(
        lambda x: parse_node_attrib(x, namespace_map, alias_map)
    )
    df["DisplayName"] = df["elem"].map(lambda x: finddisplayname(x, uaxsd))
    df["Description"] = df["elem"].map(lambda x: finddescription(x, uaxsd))
    df["References"] = df["elem"].map(
        lambda x: findrefs(x, uaxsd, namespace_map, alias_map)
    )
    df["Value"] = df["elem"].map(lambda x: findval(x, uaxsd))
    df = df.drop(columns="elem")
    return df


def iterparse_xml(
    xmlfile: str, desired_namespace_list: List[str], batchsize=100000
) -> Dict[str, Any]:
    """
    Parses the XML file to a dictionary with a nodes pd.DataFrame and an aliaslist with refrencetype aliasnames

    Parameters:
    xmlfile (str): Path to file to read.
    desired_namespace_list (List[str]): The list with namspace uris in the desired order.

    Returns:
    Dictionary (str,object): The with dictionary with pd.Dataframe in 'nodes' key and alias dict in 'alias_map' key
    Node Dataframe example:
     Tag                                             Attrib                                          References                                           ValueTmp
    ['UAVariable'    {'NodeId': '0:0:8244', 'BrowseName': 'Annotation', 'ParentNodeId': '0:0:7617', 'DataType': 'String'}   'Annotation' None

    list([('0:0:69', {'ReferenceType': 'HasTypeDefinition'}), ('0:0:7617', {'ReferenceType': 'HasComponent', 'IsForward': 'false'})])

    """
    uaxsd = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}"

    aliasnses = list(map(lambda x: uaxsd + x, ["NamespaceUris", "Uri", "Alias"]))
    namespace_list = []
    alias_map = {}

    nodeclasses = [
        "UAObjectType",
        "UAObject",
        "UAVariableType",
        "UAVariable",
        "UADataType",
        "UAReferenceType",
        "UAView",
        "UAMethod",
    ]
    nodeclasses_xsd = list(map(lambda x: uaxsd + x, nodeclasses))

    nodeset = uaxsd + "UANodeSet"

    tagiter = ET.iterparse(
        xmlfile,
        events=("start", "end"),
        tag=[nodeset] + nodeclasses_xsd + aliasnses,
        encoding="utf-8",
    )

    elems = []
    df_list = []
    i = 1
    foundnses = False
    namespace_map = {0: 0}
    xml_nsmap = {}
    for event, elem in tagiter:
        if elem.tag == nodeset:
            if event == "start":
                xml_nsmap = elem.nsmap.copy()
            if event == "end":
                pass
        elif not foundnses and event == "end" and elem.tag == uaxsd + "Uri":
            namespace_list.append(elem.text)
            elem.clear()
        elif event == "end" and elem.tag == uaxsd + "Alias":
            alias_map[elem.attrib["Alias"]] = parse_nodeid(elem.text, namespace_map)
            elem.clear()
        elif not foundnses and event == "end" and elem.tag == uaxsd + "NamespaceUris":
            # All uris in "NamespaceUris" are parsed
            foundnses = True
            extend_namespace_map(desired_namespace_list, namespace_list, namespace_map)
        elif event == "end":
            elems.append(elem)
        if i % batchsize == 0:
            logger.info(f"Processing XML node batch {i}")
            df = process_elem_batch(
                elems=elems,
                uaxsd=uaxsd,
                namespace_map=namespace_map,
                alias_map=alias_map,
            )
            df_list.append(df)
            # Release memory
            list(map(lambda x: x.clear(), elems))
            elems = []
        i = i + 1

    if len(elems) > 0:
        df = process_elem_batch(elems, uaxsd, namespace_map, alias_map)
        # Release memory
        list(map(lambda x: x.clear(), elems))
        df_list.append(df)

    nodes = pd.concat(df_list)

    return {"nodes": nodes, "alias_map": alias_map, "namespace_map": namespace_map}


def extend_namespace_map(
    existing_namespaces: List[str],
    namespace_list: List[str],
    namespace_map: Dict[int, int],
) -> None:
    """
    Extends a dictionary with ns mapping based on the order from desired_namespace_list.

    Parameters:
    desired_namespace_list (List[str]) : The list of namespaces to map to
    namespace_list (List[str]) : The list of namespaces to map from

    Returns:
    Dictionary (str,str): The mapping dictionary based on Namespace index: "From Idx":"To Idx"
    """
    if 0 not in namespace_map:
        namespace_map[0] = 0
    for i, n in enumerate(namespace_list):
        if n not in existing_namespaces:
            logger.warning(
                "Namespace "
                + n
                + " not found in namespace list, adding with index "
                + str(len(existing_namespaces))
            )
            existing_namespaces.append(n)

        namespace_map[i + 1] = existing_namespaces.index(n)


def normalize_wrt_nodeid(nodes: pd.DataFrame, references: pd.DataFrame) -> pd.DataFrame:
    logger.info("Started normalizing table structure with respect to nodeid")

    nodecols = ["NodeId", "ParentNodeId", "DataType", "MethodDeclarationId"]
    refcols = ["Src", "Trg", "ReferenceType"]

    allids = pd.concat(
        [nodes[c].dropna() for c in nodecols if c in nodes.columns.values]
        + [references[c].dropna() for c in refcols if c in references.columns.values],
        ignore_index=True,
    )
    codes, uniques = pd.factorize(allids)

    lookup_df = pd.DataFrame({"uniques": uniques})

    uniques_index = pd.Index(uniques)
    convert_to_int_index = lambda x: uniques_index.get_indexer(pd.Index(x)).astype(
        pd.Int32Dtype
    )
    for c in refcols:
        references[c] = convert_to_int_index(references[c])

    nodes["id"] = convert_to_int_index(nodes["NodeId"])
    for c in nodecols[1:]:  # Skip nodeids!
        if c in nodes.columns.values:
            nodes[c] = convert_to_int_index(nodes[c])
            nodes[c] = nodes[c].replace(-1, pd.NA)

    logger.info("Finished normalizing table structure with respect to nodeid")
    return lookup_df


def get_xml_namespaces(xml_file: str) -> List[str]:
    """Opens the xml file provided and peeks inside the file to look for any tags which
    indicate the namespace uri of the xml file.

    Args:
        xml_file (str): The full filepath to the xml file to check

    Returns:
        List[str] containing the different namespace uris which are found in the file.

    """
    uaxsd = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}"

    namespace_list = []
    # In some NodeSet2 definition files the <Model> tag is not found
    # therefore using the common files name as well.
    if xml_file.endswith("Opc.Ua.NodeSet2.xml"):
        namespace_list.append("http://opcfoundation.org/UA")
        namespace_list.append("http://opcfoundation.org/UA/")
        return namespace_list

    # Adding tags which contain Models and ModelUri.
    tree = ET.parse(xml_file)
    root = tree.getroot()

    found_nses = False
    root_iter_models = root.iter(uaxsd + "Models")
    if root_iter_models:
        for models_tag in root_iter_models:
            for model in models_tag.iter(uaxsd + "Model"):
                model_uri = model.get("ModelUri")
                if not found_nses and model_uri:
                    namespace_list.append(model_uri)
        return namespace_list

    # Adding tags which contain NamespaceUris
    tag_namespace = ET.iterparse(
        xml_file, events=("start", "end"), tag=[uaxsd + "Uri", uaxsd + "NamespaceUris"]
    )

    found_nses = False
    for event, elem in tag_namespace:
        if not found_nses and event == "end" and elem.tag == uaxsd + "Uri":
            namespace_list.append(elem.text)
            elem.clear()
        elif not found_nses and event == "end" and elem.tag == uaxsd + "NamespaceUris":
            # All uris in "NamespaceUris" are parsed
            break

    return namespace_list


def get_list_of_xml_files(xml_directory_path: str) -> List[str]:
    """Returns a list of xml_files in a provided directory

    Args:
        xml_directory_path (str): Full path to the directory

    Return:
        List[str] of xmls which are found in the directory

    """

    files = []
    for file in os.listdir(xml_directory_path):
        full_path = os.path.join(xml_directory_path, file)
        if os.path.isfile(full_path) and full_path.endswith(".xml"):
            files.append(full_path)

    return files


def exclude_files_not_in_namespaces(
    input_files: List[str], namespaces: List[str]
) -> List[str]:
    """Removes the files which do not have any NamespaceUris in the namespaces list.

    Args:
        input_files (List[str]): List of files to filter through.
        namespaces (List[str]): List of desired namespaces to keep.

    Return:
        List[str] of xmls which are found in the directory

    """
    # Removes None for the list if found in the namespaces
    namespaces_set_list = list(set(filter(None, namespaces)))
    output_files = input_files.copy()
    for file in input_files:
        file_ns_uris = get_xml_namespaces(file)
        # Removes file if none of the file_ns_uris are in namespaces_set_list
        if not any(file in file_ns_uris for file in namespaces_set_list):
            output_files.remove(file)

    return output_files


def parse_xml(
    xmlfile: Union[str, BytesIO], namespaces: Optional[List[str]] = None
) -> Dict[str, Any]:
    parse_dict = parse_xml_without_normalization(xmlfile, namespaces)
    lookup_df = normalize_wrt_nodeid(parse_dict["nodes"], parse_dict["references"])
    parse_dict["lookup_df"] = lookup_df
    return parse_dict


def parse_xml_without_normalization(
    xmlfile: Union[str, BytesIO], namespaces: Optional[List[str]] = None
) -> Dict[str, Any]:
    if namespaces is None:
        namespaces = []

    uans = "http://opcfoundation.org/UA/"
    if uans not in namespaces:
        namespaces.append(uans)

    parse_dict = iterparse_xml(xmlfile, namespaces)
    nodes = parse_dict["nodes"].reset_index()
    nodes = nodes.rename(columns={"Tag": "NodeClass"})
    nodes = pd.concat(
        [nodes, pd.DataFrame.from_records(nodes["Attrib"].values)], axis=1
    ).drop(columns="Attrib")

    references = nodes.loc[:, ["NodeId", "References"]]
    references = (
        references.rename(columns={"NodeId": "Src"})
        .explode("References")
        .reset_index(drop=True)
    )
    references = references.loc[~references["References"].isna()]

    references["Trg"] = references["References"].map(lambda x: x[0])
    references["IsForward"] = references["References"].map(
        lambda x: False
        if "IsForward" in x[1] and x[1]["IsForward"] == "false"
        else True
    )
    refsrc = references[["Src"]]
    references.loc[~references["IsForward"], "Src"] = references.loc[
        ~references["IsForward"], "Trg"
    ]
    references.loc[~references["IsForward"], "Trg"] = refsrc.loc[
        ~references["IsForward"], "Src"
    ]

    references["ReferenceType"] = references["References"].map(
        lambda x: x[1]["ReferenceType"]
    )
    references = references.drop(columns=["References", "IsForward"])
    references = references.drop_duplicates().reset_index(drop=True)
    nodes = nodes.drop(columns=["References", "index"])

    # Browsenames are prefixed with namespace indices, but this makes for difficult to follow browsepaths.
    # We keep Browsename namespaces in its own column in order not to lose this information
    namespace_map = parse_dict["namespace_map"]
    nodes["BrowseNameNamespace"] = nodes["BrowseName"].map(
        lambda x: int(x.split(":")[0]) if ":" in x else 0
    )
    nodes["BrowseNameNamespace"] = nodes["BrowseNameNamespace"].map(namespace_map)
    nodes["BrowseName"] = nodes["BrowseName"].map(
        lambda x: x.split(":")[1] if ":" in x else x
    )

    if "Value" not in nodes.columns.values:
        nodes["Value"] = None
    nodes["ns"] = nodes["NodeId"].map(lambda x: x.namespace).astype(pd.Int8Dtype())
    return {"nodes": nodes, "references": references, "namespaces": namespaces}


def parse_xml_dir(
    xml_dir: str, namespaces: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Parses xml directory and creates Pandas tables which contains
    a consolidated nodes, references, namespaces, and lookup_df
    for the files found in the nodes. It will create a list of xml files
    contained in the xml directory. If the 'namespaces' parameter is
    provided, it will not include files with namespaces which are not
    found in the namespace list.

    Args:
        xml_dir (str): Full path to the directory of xmls
        namespaces (Optional[List[str]] = None): Dictionary of namespaces

    Return:
        Dict[str, Any] of parsed pandas tables from the xml directories.

    """

    files = get_list_of_xml_files(xml_dir)
    return parse_xml_files(files, namespaces)


def parse_xml_files(
    files: List[str], namespaces: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Parses xml list of files and creates Pandas tables which contains
    a consolidated nodes, references, namespaces, and lookup_df
    for the files found in the nodes. It will create a list of xml files
    contained in the xml directory. If the 'namespaces' parameter is
    provided, it will not include files with namespaces which are not
    found in the namespace list.

    Args:
        files (str): Full path of xml files
        namespaces (Optional[List[str]] = None): Dictionary of namespaces

    Return:
        Dict[str, Any] of parsed pandas tables from the xml directories.

    """

    if namespaces:
        files = exclude_files_not_in_namespaces(files, namespaces)

    if namespaces is None:
        namespaces = []
    df_nodes_list = []
    df_references_list = []

    files.sort()
    for file in files:
        if not file.endswith(".xml"):
            continue
        if not os.path.exists(file):
            raise FileNotFoundError(
                "The specified xml file does not exist or incorrect path was provided"
            )

        logger.info("Started parsing " + str(file))
        parse_dict = parse_xml_without_normalization(file, namespaces)
        namespaces = parse_dict["namespaces"]
        df_nodes_list.append(parse_dict["nodes"])
        df_references_list.append((parse_dict["references"]))
        logger.info("Finished parsing " + str(file))

    nodes = pd.concat(df_nodes_list, ignore_index=True)
    references = pd.concat(df_references_list, ignore_index=True)
    lookup_df = normalize_wrt_nodeid(nodes, references)
    return {
        "nodes": nodes,
        "references": references,
        "namespaces": namespaces,
        "lookup_df": lookup_df,
    }

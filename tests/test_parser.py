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
from pathlib import Path

import pandas as pd
from definitions import get_project_root

import opcua_tools as ot
from opcua_tools.json_parser.parse import pre_process_xml_to_json
from opcua_tools.nodeset_parser import (
    exclude_files_not_in_namespaces,
    get_list_of_xml_files,
    get_xml_namespaces,
)

PATH_HERE = os.path.dirname(__file__)


def test_parsing_without_errors():
    xml_dir = PATH_HERE + "/testdata/parser"
    files = get_list_of_xml_files(xml_dir)
    for f in files:
        pre_process_xml_to_json(f)
    ot.parse_xml_dir(xml_dir)


def test_parse_nodeid():
    s = "ns=1;i=0"
    nid = ot.parse_nodeid(s)

    assert type(nid.value) == str


def test_parser_easy_example_stays_put():
    gr = ot.UAGraph.from_path(PATH_HERE + "/testdata/generator")
    nodes = gr.get_normalized_nodes_df()
    references = gr.get_normalized_references_df()

    nodes.to_csv(PATH_HERE + "/expected/parser/nodes.csv", index=False)
    references.to_csv(PATH_HERE + "/expected/parser/references.csv", index=False)

    actual_nodes = pd.read_csv(PATH_HERE + "/expected/parser/nodes.csv")
    actual_references = pd.read_csv(PATH_HERE + "/expected/parser/references.csv")

    expected_nodes = pd.read_csv(
        PATH_HERE + "/expected/parser/expected_nodes.csv",
        dtype={"IsAbstract": bool, "Symmetric": bool},
    )
    expected_references = pd.read_csv(
        PATH_HERE + "/expected/parser/expected_references.csv"
    )

    pd.testing.assert_frame_equal(expected_references, actual_references)

    for c in expected_nodes.columns:
        if c != "Value":
            pd.testing.assert_series_equal(expected_nodes[c], actual_nodes[c])
        else:
            # Todo fix test error for value between linux/windows
            pass


def test_parse_file_list():
    path_to_xmls = str(Path(PATH_HERE) / "testdata" / "parser")
    xml_list = []
    for xml in os.listdir(path_to_xmls):
        full_xml_path = os.path.join(path_to_xmls, xml)
        if os.path.isfile(full_xml_path):
            xml_list.append(full_xml_path)

    parse_dict = ot.parse_xml_files(xml_list)
    assert "nodes" in parse_dict
    assert "references" in parse_dict
    assert "namespaces" in parse_dict
    assert "lookup_df" in parse_dict
    assert "models" in parse_dict


def test_parse_no_namespace_list(paper_example_path):
    path_to_xmls = str(paper_example_path)
    ua_graph = ot.UAGraph.from_path(path_to_xmls)

    # Checking that content is in correct namespace
    i_scd_ca_row = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "I_SCD_CA"]
    oil_and_gas_system_row = ua_graph.nodes[
        ua_graph.nodes["DisplayName"] == "OilAndGasSystemType"
    ]
    site1_row = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "Site1"]

    assert i_scd_ca_row["ns"].values[0] == 3
    assert oil_and_gas_system_row["ns"].values[0] == 2
    assert site1_row["ns"].values[0] == 1


def test_parse_regular_namespace_list(paper_example_path):
    namespace_dict = {
        0: "http://opcfoundation.org/UA/",
        1: "http://prediktor.no/apis/ua/",
        2: "http://prediktor.com/paper_example",
        3: "http://prediktor.com/iec63131_fragment",
        4: "http://prediktor.com/RDS-OG-Fragment",
    }
    path_to_xmls = str(paper_example_path)
    ua_graph = ot.UAGraph.from_path(path_to_xmls, namespace_dict)

    # Checking that content is in correct namespace
    i_scd_ca_row = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "I_SCD_CA"]
    oil_and_gas_system_row = ua_graph.nodes[
        ua_graph.nodes["DisplayName"] == "OilAndGasSystemType"
    ]
    site1_row = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "Site1"]

    assert i_scd_ca_row["ns"].values[0] == 3
    assert oil_and_gas_system_row["ns"].values[0] == 4
    assert site1_row["ns"].values[0] == 2


def test_parse_scattered_namespace_list(paper_example_path):
    namespace_dict = {
        0: "http://opcfoundation.org/UA/",
        7: "http://prediktor.no/apis/ua/",
        8: "http://prediktor.com/paper_example",
        3: "http://prediktor.com/iec63131_fragment",
        6: "http://prediktor.com/RDS-OG-Fragment",
    }
    path_to_xmls = str(paper_example_path)
    ua_graph = ot.UAGraph.from_path(path_to_xmls, namespace_dict)

    # Checking that content is in correct namespace
    i_scd_ca_row = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "I_SCD_CA"]
    oil_and_gas_system_row = ua_graph.nodes[
        ua_graph.nodes["DisplayName"] == "OilAndGasSystemType"
    ]
    site1_row = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "Site1"]

    assert i_scd_ca_row["ns"].values[0] == 3
    assert oil_and_gas_system_row["ns"].values[0] == 6
    assert site1_row["ns"].values[0] == 8


def test_get_xml_namespaces():
    test_parser_data = get_project_root() / "tests" / "testdata" / "parser"

    files = [
        str(test_parser_data / "Opc.ISA95.NodeSet2.xml"),
        str(test_parser_data / "Opc.Ua.IEC61850-6.NodeSet2.xml"),
        str(test_parser_data / "Opc.Ua.IEC61850-7-4.NodeSet2.xml"),
    ]

    expected_namespaces = {
        "http://www.OPCFoundation.org/UA/2013/01/ISA95",
        "http://opcfoundation.org/UA/IEC61850-6",
        "http://opcfoundation.org/UA/IEC61850-7-4",
    }

    namespace_set = set()
    for xml_file in files:
        namespace_uri_list = get_xml_namespaces(xml_file)
        namespace_set = namespace_set.union(set(namespace_uri_list))

    assert expected_namespaces == namespace_set


def test_get_list_of_xml_files():
    xml_directory = str(get_project_root() / "tests" / "testdata" / "parser")
    expected_xml_files = {
        os.path.join(xml_directory, "Opc.ISA95.NodeSet2.xml"),
        os.path.join(xml_directory, "Opc.Ua.IEC61850-6.NodeSet2.xml"),
        os.path.join(xml_directory, "Opc.Ua.IEC61850-7-3.NodeSet2.xml"),
        os.path.join(xml_directory, "Opc.Ua.IEC61850-7-4.NodeSet2.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part10.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part11.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part12.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part13.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part14.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part17.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part19.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part3.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part4.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part5.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part8.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part9.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Services.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.xml"),
    }

    actual_xml_files = set(get_list_of_xml_files(xml_directory))
    d = expected_xml_files.difference(actual_xml_files)
    print(d)
    assert expected_xml_files == actual_xml_files


def test_namespace_dict_parse_xml_dict():
    xml_directory = str(get_project_root() / "tests" / "testdata" / "parser")
    input_namespaces = [
        "http://opcfoundation.org/UA/",
        "http://www.OPCFoundation.org/UA/2013/01/ISA95",
        "http://opcfoundation.org/UA/IEC61850-7-4",
    ]
    expected_files = {
        os.path.join(xml_directory, "Opc.ISA95.NodeSet2.xml"),
        os.path.join(xml_directory, "Opc.Ua.IEC61850-7-4.NodeSet2.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part10.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part11.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part12.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part13.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part14.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part17.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part19.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part3.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part4.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part5.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part8.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Part9.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.Services.xml"),
        os.path.join(xml_directory, "Opc.Ua.NodeSet2.xml"),
    }

    xml_files = get_list_of_xml_files(xml_directory)
    xml_files = exclude_files_not_in_namespaces(xml_files, input_namespaces)

    assert expected_files == set(xml_files)

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

import opcua_tools as ot
import os
import pandas as pd
from pathlib import Path
PATH_HERE = os.path.dirname(__file__)


def test_parsing_without_errors():
    ot.parse_xml_dir(PATH_HERE + '/testdata/parser')

def test_parse_nodeid():
    s = 'ns=1;i=0'
    nid = ot.parse_nodeid(s)

    assert type(nid.value) == str

def test_parser_easy_example_stays_put():
    gr = ot.UAGraph.from_path(PATH_HERE + '/testdata/generator')
    nodes = gr.get_normalized_nodes_df()
    references = gr.get_normalized_references_df()

    nodes.to_csv(PATH_HERE + '/expected/parser/nodes.csv', index=False)
    references.to_csv(PATH_HERE + '/expected/parser/references.csv', index=False)

    actual_nodes = pd.read_csv(PATH_HERE + '/expected/parser/nodes.csv')
    actual_references = pd.read_csv(PATH_HERE + '/expected/parser/references.csv')

    expected_nodes = pd.read_csv(PATH_HERE + '/expected/parser/expected_nodes.csv')
    expected_references = pd.read_csv(PATH_HERE + '/expected/parser/expected_references.csv')

    pd.testing.assert_frame_equal(expected_references, actual_references)

    for c in expected_nodes.columns:
        if c != 'Value':
            pd.testing.assert_series_equal(expected_nodes[c], actual_nodes[c])
        else:
            #Todo fix test error for value between linux/windows
            pass


def test_parse_file_list():
    path_to_xmls = str(Path(PATH_HERE) / "testdata" / "parser")
    xml_list = []
    for xml in os.listdir(path_to_xmls):
        full_xml_path = os.path.join(path_to_xmls, xml)
        if os.path.isfile(full_xml_path):
            xml_list.append(full_xml_path)

    ot.parse_xml_files(xml_list)


def test_parse_no_namespace_list():
    path_to_xmls = str(Path(PATH_HERE) / "testdata" / "paper_example")
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


def test_parse_regular_namespace_list():
    namespace_dict = {
        0: "http://opcfoundation.org/UA/",
        1: "http://prediktor.no/apis/ua/",
        2: "http://prediktor.com/paper_example",
        3: "http://prediktor.com/iec63131_fragment",
        4: "http://prediktor.com/RDS-OG-Fragment",
    }
    path_to_xmls = str(Path(PATH_HERE) / "testdata" / "paper_example")
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


def test_parse_scattered_namespace_list():
    namespace_dict = {
        0: "http://opcfoundation.org/UA/",
        7: "http://prediktor.no/apis/ua/",
        8: "http://prediktor.com/paper_example",
        3: "http://prediktor.com/iec63131_fragment",
        6: "http://prediktor.com/RDS-OG-Fragment",
    }
    path_to_xmls = str(Path(PATH_HERE) / "testdata" / "paper_example")
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

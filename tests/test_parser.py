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

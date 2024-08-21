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

import pytest
from definitions import get_project_root

import opcua_tools as ot
from opcua_tools.json_parser.parse import pre_process_xml_to_json
from opcua_tools.nodeset_parser import get_list_of_xml_files

PATH_HERE = os.path.dirname(__file__)


@pytest.fixture
def circular_uag():
    namespace_dict = {
        0: "http://opcfoundation.org/UA/",
        1: "http://test.org/Circular/",
    }
    xml_directory = str(get_project_root() / "tests" / "testdata" / "circular")
    for f in get_list_of_xml_files(xml_directory):
        pre_process_xml_to_json(f)
    return ot.UAGraph.from_path(xml_directory, namespace_dict)


def test_get_normalized_references(circular_uag):
    uag = circular_uag
    normalized_refs = uag.get_normalized_references_df("http://test.org/Circular/")
    length = len(normalized_refs)
    assert length == 12


def test_find_circular_reference_nodes(circular_uag):
    uag = circular_uag
    circular_refs = uag.find_circular_reference_nodes("http://test.org/Circular/")
    assert len(circular_refs) == 4
    assert str(circular_refs["NodeId"].values[0]) == "ns=1;i=5006"
    assert str(circular_refs["NodeId"].values[1]) == "ns=1;i=5003"
    assert str(circular_refs["NodeId"].values[2]) == "ns=1;i=5005"
    assert str(circular_refs["NodeId"].values[3]) == "ns=1;i=5004"

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

import pandas as pd
import pytest
from definitions import get_project_root

from opcua_tools import ua_data_types, value_parser
from opcua_tools.ua_graph import UAGraph


@pytest.fixture(scope="session")
def boolean_test_data():
    df_values = [
        ["Boolean", "false", False],
        ["Boolean", "False", False],
        ["Boolean", "true", True],
        ["Boolean", "True", True],
    ]
    data = pd.DataFrame(df_values, columns=["tag_type", "input", "solution"])
    return data


@pytest.fixture(scope="session")
def ua_graph(paper_example_path):
    ua_graph = UAGraph.from_path(str(paper_example_path))
    return ua_graph


def test_parse_boolean(boolean_test_data):
    """Ensuring that the parse_boolean function in value_parser.py
    will properly deal with upper and lower case representations of
    strings in python."""

    data = boolean_test_data.copy()
    data["dataclass"] = data["input"].apply(
        lambda value: value_parser.parse_boolean(value)
    )
    data["output"] = data["dataclass"].apply(lambda bool_class: bool_class.value)
    pd.testing.assert_series_equal(data["output"], data["solution"], check_names=False)


def test_proper_initiation_of_eurange_class_when_reading_xml(ua_graph):
    """Ensuring that the parse EURange parsing in value_parser.py
    will properly read the EURange in the XML."""

    eurange_nodes = ua_graph.nodes[ua_graph.nodes["DisplayName"] == "EURange"]
    non_none_eurange_nodes = eurange_nodes[~(eurange_nodes["Value"].isnull())]
    non_none_eurange_values = non_none_eurange_nodes["Value"]
    assert non_none_eurange_values.apply(
        lambda value: isinstance(value, ua_data_types.UAEURange)
    ).all()


def test_ua_graph_xml_encode_for_eurange(ua_graph):
    """Test checks that the UAEURange is correctly encoded when
    'xml_encode()' is run."""
    output_folder = get_project_root() / "tests" / "output"
    output_file_path = str(output_folder / "nodeset_eurange_output.xml")

    # Creating output folder if it does not exist
    if not os.path.exists(str(output_folder)):
        os.makedirs(str(output_folder))

    ua_graph.write_nodeset(
        output_file_path,
        "http://prediktor.com/paper_example",
    )

    path_to_tests = get_project_root() / "tests"
    expected_file_path = str(
        path_to_tests / "expected" / "value_parser" / "expected_nodeset_eurange.xml"
    )

    expected_eurange_xml_lines = []
    with open(expected_file_path) as expected_file:
        for line in expected_file:
            if "ns=1;i=40" in line or "ns=1;i=31" in line:
                expected_eurange_xml_lines.append(line)

    output_eurange_xml_lines = []
    with open(output_file_path) as output_file:
        for line in output_file:
            if "ns=1;i=40" in line or "ns=1;i=31" in line:
                output_eurange_xml_lines.append(line)

    assert set(output_eurange_xml_lines) == set(expected_eurange_xml_lines)


def test_cached_parse_nodeid_parse_node_with_equal_sign_in_value():
    nodeid = "ns=5;s=<MySite>=A1"
    expected_output = (5, ua_data_types.NodeIdType.STRING, "<MySite>=A1")
    assert value_parser.cached_parse_nodeid(nodeid) == expected_output

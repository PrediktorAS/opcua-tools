# Copyright 2022 Prediktor AS
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

import pandas as pd
import opcua_tools as ot
from opcua_tools.ua_data_types import NodeIdType, UANodeId


def test_create_node_paths_by_reference_types(paper_example_path, ua_graph_data_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    hierarchical_references = [
        "HasComponent",
        "HasProperty",
        "HasChild",
        "Organizes",
        "ProductAspect",
    ]
    new_hierarchical_paths = ua_graph.create_node_paths_by_reference_types(
        root_node_browsename="Site1",
        hierarchical_reference_types=hierarchical_references,
    )
    # Writing node_paths to file in order to avoid differences in reading expected nodes
    output_nodes_paths_data_path = (
        ua_graph_data_path / "output" / "output_node_paths.csv"
    )
    new_hierarchical_paths.to_csv(
        str(output_nodes_paths_data_path),
        float_format="{:f}".format,
        encoding="utf-8",
    )

    expected_nodes_paths_data_path = (
        ua_graph_data_path / "expected" / "expected_node_paths.csv"
    )
    expected_nodes_paths = pd.read_csv(str(expected_nodes_paths_data_path))
    output_nodes_paths = pd.read_csv(str(output_nodes_paths_data_path))

    pd.testing.assert_frame_equal(expected_nodes_paths, output_nodes_paths)


def test_ua_graph_reference_type_by_browsename(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    reference_types = ua_graph.reference_type_by_browsename("HasComponent")
    assert reference_types == 48


def test_ua_graph_object_type_by_browsename(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    object_types = ua_graph.object_type_by_browsename("DataTypeSystemType")
    assert object_types == 69


def test_ua_graph_variable_type_by_browsename(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    variable_types = ua_graph.variable_type_by_browsename("BaseVariableType")
    assert variable_types == 59


def test_ua_graph_data_type_by_browsename(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    data_types = ua_graph.data_type_by_browsename("Number")
    assert data_types == 3


def test_ua_graph_object_by_browsename(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    objects = ua_graph.object_by_browsename("Site1")
    assert objects == 3909


def test_ua_graph_nodeid_by_browsename_without_nodeclass(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    nodeid = ua_graph.nodeid_by_browsename("I_SCD_CA")
    expected_nodeid = UANodeId(namespace=3, nodeid_type=NodeIdType("i"), value="1035")
    assert nodeid == expected_nodeid

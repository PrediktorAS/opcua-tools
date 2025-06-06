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

import os
from pathlib import Path

import pandas as pd
import pytest

import opcua_tools as ot
from opcua_tools.ua_data_types import NodeIdType, UANodeId

PATH_HERE = os.path.dirname(__file__)


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


def test_ua_graph_get_instances_with_type_info(paper_example_path):
    ua_graph = ot.UAGraph.from_path(str(paper_example_path))

    references = ua_graph.get_instances_with_type_info()
    # references.to_csv(
    #     os.path.join(PATH_HERE, "expected", "ua_graph", "references.csv"),
    #     index=False
    # )
    output_references_path = os.path.join(PATH_HERE, "output", "output_references.csv")
    references.to_csv(output_references_path, index=False)
    output_references = pd.read_csv(output_references_path)

    expected_references = pd.read_csv(
        os.path.join(PATH_HERE, "expected", "ua_graph", "references.csv")
    )

    pd.testing.assert_frame_equal(expected_references, output_references)


def test_ua_graph_should_not_be_instantiated_when_some_target_nodes_are_missing():
    file_paths = [
        str(Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.IEC61850-6.NodeSet2.xml"),
        str(Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.NodeSet2.xml"),
    ]

    with pytest.raises(ValueError) as e:
        ot.UAGraph.from_file_list(file_paths)

    assert (
        str(e.value)
        == "Some target ids do not exist.\nThese are the source nodes with missing target nodes:\n  DisplayName (source) NodeId (source) DisplayName (reference) NodeId (reference)\n0                 <LN>        ns=2;i=9       HasTypeDefinition               i=40\n1                 <LN>       ns=2;i=12       HasTypeDefinition               i=40\n2                 <LN>       ns=2;i=14       HasTypeDefinition               i=40\n3                 <LN>       ns=2;i=17       HasTypeDefinition               i=40\n4              <LNode>       ns=2;i=40       HasTypeDefinition               i=40"
    )


def test_ua_graph_should_not_be_instantiated_when_some_source_nodes_are_missing():
    file_paths = [
        str(Path(PATH_HERE) / "testdata" / "paper_example" / "rds_og_fragment.xml"),
        str(Path(PATH_HERE) / "testdata" / "paper_example" / "iec63131_fragment.xml"),
    ]

    with pytest.raises(ValueError) as e:
        ot.UAGraph.from_file_list(file_paths)

    assert (
        str(e.value)
        == "Some source ids do not exist.\nThese are the target nodes with missing source nodes:\n  DisplayName (target)          NodeId (target) DisplayName (reference) NodeId (reference)\n0    GeneralSystemType               ns=2;s=SYS                    <NA>                NaN\n1             SiteType          ns=2;s=SiteType                    <NA>                NaN\n2     FunctionalAspect  ns=2;s=FunctionalAspect                    <NA>                NaN\n3        ProductAspect     ns=2;s=ProductAspect                    <NA>                NaN"
    )


def test_ua_graph_with_nested_nodeid_value():
    file_paths = [
        str(Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.NodeSet2.xml"),
        str(
            Path(PATH_HERE)
            / "testdata"
            / "parser"
            / "nested_nodeid"
            / "nested_nodeid.xml"
        ),
    ]

    graph = ot.UAGraph.from_file_list(file_paths)

    requested_variable = graph.nodes[graph.nodes["BrowseName"] == "NestedNodeId"]
    requested_variable_value = requested_variable.iloc[0]["Value"]
    assert requested_variable_value == UANodeId(
        namespace=0, nodeid_type=NodeIdType.NUMERIC, value="0"
    )


def test_ua_graph_can_be_created_with_nodeset2_file_without_nodes():
    file_paths = [
        str(Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.NodeSet2.xml"),
        str(
            Path(PATH_HERE)
            / "testdata"
            / "invalid_example"
            / "empty_nodeset2_file"
            / "nodeset2_file_with_no_nodes.xml"
        ),
        str(
            Path(PATH_HERE)
            / "testdata"
            / "invalid_example"
            / "empty_nodeset2_file"
            / "nodeset2_file_with_no_nodes_2.xml"
        ),
        str(Path(PATH_HERE) / "testdata" / "paper_example" / "rds_og_fragment.xml"),
    ]

    graph = ot.UAGraph.from_file_list(file_paths)

    assert graph.namespaces == [
        "http://opcfoundation.org/UA/",
        "http://prediktor.com/RDS-OG-Fragment",
    ]

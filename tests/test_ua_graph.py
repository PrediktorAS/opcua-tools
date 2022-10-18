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

import opcua_tools as ot
import pandas as pd


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

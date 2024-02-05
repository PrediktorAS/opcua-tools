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

from definitions import get_project_root

import opcua_tools as ot
from opcua_tools.nodeset_generator import (
    denormalize_nodes_nodeids,
    denormalize_references_nodeids,
)


def test_values_correct(paper_example_path):
    parse_dict = ot.parse_xml_dir(str(paper_example_path))

    nodes = parse_dict["nodes"]
    references = parse_dict["references"]
    lookup_df = parse_dict["lookup_df"]
    nodes = denormalize_nodes_nodeids(nodes, lookup_df)
    denormalize_references_nodeids(references, lookup_df)
    nodes = nodes.drop(columns=["id"])
    nodes = nodes.sort_values(by=nodes.columns.values.tolist()).reset_index(drop=True)

    nodes = nodes[nodes["ns"] == 1]  # Select only example namespace.

    output_path = (
        get_project_root() / "tests" / "expected" / "paper_example" / "nodes.csv"
    )
    nodes.to_csv(str(output_path), index=False)

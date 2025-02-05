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
from pathlib import Path
from unittest import mock

import pandas as pd
from definitions import get_project_root

import opcua_tools as ot
from opcua_tools import UAGraph
from opcua_tools.json_parser.parse import pre_process_xml_to_json
from opcua_tools.nodeset_generator import (
    create_header_xml,
    denormalize_nodes_nodeids,
    denormalize_references_nodeids,
)
from opcua_tools.nodeset_parser import get_list_of_xml_files

PATH_HERE = os.path.dirname(__file__)


def test_idempotency():
    xml_dir = PATH_HERE + "/testdata/generator"
    files = get_list_of_xml_files(xml_dir)
    for f in files:
        pre_process_xml_to_json(f)
    parse_dict = ot.parse_xml_dir(xml_dir)
    ot.create_nodeset2_file(
        nodes=parse_dict["nodes"].copy(),
        references=parse_dict["references"].copy(),
        models=parse_dict["models"].copy(),
        namespaces=parse_dict["namespaces"],
        serialize_namespace=0,
        filename_or_stringio=PATH_HERE + "/expected/generator/nodeset2.xml",
    )
    xml_dir = PATH_HERE + "/expected/generator"
    files = get_list_of_xml_files(xml_dir)
    for f in files:
        pre_process_xml_to_json(f)

    parse_dict2 = ot.parse_xml_dir(PATH_HERE + "/expected/generator")

    nodes = parse_dict["nodes"]
    references = parse_dict["references"]
    nodes = denormalize_nodes_nodeids(nodes, parse_dict["lookup_df"])
    references = denormalize_references_nodeids(references, parse_dict["lookup_df"])
    nodes = nodes.drop(columns=["id"])
    nodes = nodes.sort_values(by=nodes.columns.values.tolist()).reset_index(drop=True)
    references = references.sort_values(
        by=references.columns.values.tolist()
    ).reset_index(drop=True)

    nodes2 = parse_dict2["nodes"]
    references2 = parse_dict2["references"]
    nodes2 = denormalize_nodes_nodeids(nodes2, parse_dict2["lookup_df"])
    references2 = denormalize_references_nodeids(references2, parse_dict2["lookup_df"])
    nodes2 = nodes2.drop(columns=["id"])
    nodes2 = nodes2.sort_values(by=nodes.columns.values.tolist()).reset_index(drop=True)
    references2 = references2.sort_values(
        by=references.columns.values.tolist()
    ).reset_index(drop=True)

    # print(set(nodes['Value'].tolist()).difference(set(nodes2['Value'].tolist())))

    # print(nodes[nodes['DataType'].values != nodes2['DataType'].values][['NodeId', 'DataType']])
    # print(nodes2[nodes2['DataType'].values != nodes['DataType'].values][['NodeId', 'DataType']])

    assert set(nodes.columns.values.tolist()) == set(nodes2.columns.values.tolist())

    nodes2 = nodes2[nodes.columns.values.tolist()].copy()
    # nodes2.to_csv('nodes2.csv')
    # nodes.to_csv('nodes.csv')
    pd.testing.assert_frame_equal(nodes, nodes2)
    pd.testing.assert_frame_equal(references, references2)

    os.remove(PATH_HERE + "/expected/generator/nodeset2.xml")


def test_ua_graph_write_nodeset_without_crash(paper_example_path):
    files = get_list_of_xml_files(paper_example_path)
    for f in files:
        pre_process_xml_to_json(f)

    path_to_xmls = str(paper_example_path)
    ua_graph = UAGraph.from_path(path_to_xmls)

    output_folder = get_project_root() / "tests" / "output"
    output_file_path = str(output_folder / "paper_example_output.xml")

    # Creating output folder if it does not exist
    if not os.path.exists(str(output_folder)):
        os.makedirs(str(output_folder))

    ua_graph.write_nodeset(output_file_path, "http://prediktor.com/paper_example")


@mock.patch("opcua_tools.nodeset_generator.create_required_models")
def test_ua_graph_write_nodeset_with_required_models(create_required_models_mock):
    file_paths = [
        str(Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.IEC61850-6.NodeSet2.xml"),
        str(Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.NodeSet2.xml"),
        str(
            Path(PATH_HERE) / "testdata" / "parser" / "Opc.Ua.IEC61850-7-3.NodeSet2.xml"
        ),
    ]
    for file_path in file_paths:
        pre_process_xml_to_json(file_path)

    ua_graph = UAGraph.from_file_list(file_paths)

    output_folder = get_project_root() / "tests" / "output"
    output_file_path = str(output_folder / "required_models_output.xml")

    # Creating output folder if it does not exist
    if not os.path.exists(str(output_folder)):
        os.makedirs(str(output_folder))

    namespace_uri = "http://opcfoundation.org/UA/IEC61850-6"
    ua_graph.write_nodeset(output_file_path, namespace_uri)

    create_required_models_mock.assert_called_once_with(
        {
            "uri": "http://opcfoundation.org/UA/IEC61850-6",
            "publication_date": "2018-02-05T00:00:00Z",
            "version": "2.0",
            "required_models": [
                {
                    "uri": "http://opcfoundation.org/UA/IEC61850-7-3",
                    "publication_date": None,
                    "version": "2.0",
                },
                {
                    "uri": "http://opcfoundation.org/UA/",
                    "publication_date": "2019-05-01T00:00:00Z",
                    "version": "1.04",
                },
            ],
        }
    )


def test_create_header_sets_optional_new_model_version_properly():
    """
    Test that the create_header function sets the optional new_model_version
    """
    models = [
        {
            "uri": "http://opcfoundation.org/UA/IEC61850-6",
            "publication_date": "2018-02-05T00:00:00Z",
            "version": None,
            "required_models": [
                {
                    "uri": "http://opcfoundation.org/UA/IEC61850-7-3",
                    "publication_date": None,
                    "version": "2.0",
                },
                {
                    "uri": "http://opcfoundation.org/UA/",
                    "publication_date": "2019-05-01T00:00:00Z",
                    "version": "1.04",
                },
            ],
        },
    ]
    namespaces = ["http://opcfoundation.org/UA/IEC61850-6"]
    new_model_version = "2.0.25"
    header = create_header_xml(
        namespaces=namespaces,
        serialize_namespace=0,
        models=models,
        new_model_version=new_model_version,
    )
    version_pattern = re.compile(r"Version=\"(.+)\"")
    match = version_pattern.search(header)
    output_model_version_from_file = match.group(1)
    assert output_model_version_from_file == new_model_version

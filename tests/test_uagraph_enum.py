import os

import pytest
from definitions import get_project_root

from opcua_tools import UAEnumeration, UAGraph, UAInt32
from opcua_tools.json_parser.parse import pre_process_xml_to_json
from opcua_tools.nodes_manipulation import transform_ints_to_enums
from opcua_tools.nodeset_parser import get_list_of_xml_files, parse_xml_files


@pytest.fixture(scope="session")
def ua_graph(paper_example_path):
    path_to_xmls = str(paper_example_path)
    for f in get_list_of_xml_files(path_to_xmls):
        pre_process_xml_to_json(f)
    ua_graph = UAGraph.from_path(path_to_xmls)
    transform_ints_to_enums(ua_graph)
    return ua_graph


def test_basic_ua_graph_from_path(ua_graph):
    """From checking the data previously, we found that there are 251 UAVariables
    which point to enumeration data types. Out of these 84 of then do not contain
    an Int64 value, but 'None' instead. This means the number of UAEnumeration
    classes in the Values column, should be 167 after running the
    transform_ints_to_enums()."""

    ua_enumeration_mask = ua_graph.nodes["Value"].apply(
        lambda value: isinstance(value, UAEnumeration)
    )
    ua_enumeration_sum = ua_enumeration_mask.sum()

    assert ua_enumeration_sum == 168


@pytest.mark.run
def test_enum_ua_graph_xml_encode(ua_graph):
    """Test checks that the UAEnumeration is correctly encoded as an Int32
    when 'xml_encode()' is run. This should occur as the UAEnumeration is an
    inherited class of UAInt32.
    """
    output_folder = get_project_root() / "tests" / "output"
    output_file_path = str(output_folder / "nodeset_enum_output.xml")

    # Creating output folder if it does not exist
    if not os.path.exists(str(output_folder)):
        os.makedirs(str(output_folder))

    ua_graph.write_nodeset(output_file_path, "http://prediktor.com/paper_example")

    pre_process_xml_to_json(output_file_path)

    # Reading the file back in, without transforming to enumerations
    parse_dict = parse_xml_files([output_file_path])
    nodes = parse_dict["nodes"]

    # Getting nodes which correspond to the enum test node
    enum_test_node = nodes[nodes["DisplayName"] == "EnumTest"]

    # It should be read correctly read as UAInt32 and thus
    # the output was writing was to UAInt32
    assert type(enum_test_node["Value"].values[0]) == UAInt32

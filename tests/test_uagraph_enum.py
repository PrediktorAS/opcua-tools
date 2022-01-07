import os
import pytest
from opcua_tools.nodes_manipulation import transform_ints_to_enums
from opcua_tools import UAGraph, UAEnumeration
from definitions import get_project_root


@pytest.fixture(scope="session")
def ua_graph():
    path_to_xmls = str(get_project_root() / "tests" / "testdata" / "paper_example")
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


def test_enum_ua_graph_xml_encode(ua_graph):
    output_folder = get_project_root() / "tests" / "output"
    output_file_path = str(output_folder / "nodeset_enum_output.xml")

    # Creating output folder if it does not exist
    if not os.path.exists(str(output_folder)):
        os.makedirs(str(output_folder))

    ua_graph.write_nodeset(output_file_path, "http://prediktor.com/paper_example")

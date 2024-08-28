import os.path

from definitions import get_project_root

from opcua_tools import nodeset_parser
from opcua_tools.json_parser import namespaces, parse


def test_get_namespace_data_should_process_opcua_file_regardless_file_name():
    example_xml_path = os.path.join(
        get_project_root(),
        "tests",
        "testdata",
        "invalid_example",
        "opcua_file_with_different_name",
        "OpcUA_cut.xml",
    )
    parse.pre_process_xml_to_json(example_xml_path)

    example_json_path = f"{example_xml_path}_parsed.json"

    ns_data = namespaces.get_namespace_data_from_file(example_json_path)

    assert ns_data == {
        "included_namespaces": set(),
        "name": "http://opcfoundation.org/UA/",
    }

import os.path

from definitions import get_project_root

from opcua_tools import nodeset_parser


def test_get_namespace_data_from_file():
    example_xml_path = os.path.join(
        get_project_root(),
        "tests",
        "testdata",
        "parser",
        "Opc.Ua.IEC61850-7-4.NodeSet2.xml",
    )

    ns_data = nodeset_parser.get_namespace_data_from_file(example_xml_path)

    assert ns_data == {
        "included_namespaces": {
            "http://opcfoundation.org/UA/",
            "http://opcfoundation.org/UA/IEC61850-7-3",
        },
        "name": "http://opcfoundation.org/UA/IEC61850-7-4",
    }


def test_get_namespace_data_should_have_empty_namespaces_data_regardless_file_name():
    example_xml_path = os.path.join(
        get_project_root(),
        "tests",
        "testdata",
        "parser",
        "Opc.Ua.NodeSet2.Services.xml",
    )

    ns_data = nodeset_parser.get_namespace_data_from_file(example_xml_path)

    assert ns_data == {
        "included_namespaces": set(),
        "name": "http://opcfoundation.org/UA/",
    }

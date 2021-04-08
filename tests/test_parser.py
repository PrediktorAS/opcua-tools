import opcua_tools as ot
import os
PATH_HERE = os.path.dirname(__file__)


def test_parsing_without_errors():
    ot.parse_xml_dir(PATH_HERE + '/testdata/parser')


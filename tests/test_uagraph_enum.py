from opcua_tools.nodes_manipulation import transform_ints_to_enums
from opcua_tools import UAEnumeration
import opcua_tools as ot
from definitions import get_project_root


def test_basic_uagraph_from_path():
    """From checking the data previously, we found that there are 251 UAVariables
    which point to enumeration data types. Out of these 84 of then do not contain
    an Int64 value, but 'None' instead. This means the number of UAEnumeration
    classes in the Values column, should be 167 after running the
    transform_ints_to_enums()."""

    path_to_xmls = str(get_project_root() / "tests" / "testdata" / "paper_example")
    ua_graph = ot.UAGraph.from_path(path_to_xmls)
    transform_ints_to_enums(ua_graph)
    ua_enumeration_mask = ua_graph.nodes["Value"].apply(
        lambda value: isinstance(value, UAEnumeration)
    )
    ua_enumeration_sum = ua_enumeration_mask.sum()

    assert ua_enumeration_sum == 167

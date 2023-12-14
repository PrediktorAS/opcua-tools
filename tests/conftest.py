import pathlib

import pandas as pd
import pytest

from opcua_tools.ua_data_types import NodeIdType, UAEURange, UANodeId
from opcua_tools.definitions import get_project_root


@pytest.fixture(scope="session")
def paper_example_path():
    return get_project_root() / "tests" / "testdata" / "paper_example"


@pytest.fixture(scope="session")
def invalid_files_root_path() -> pathlib.PosixPath:
    return get_project_root() / "tests" / "testdata" / "invalid_example"


@pytest.fixture(scope="session")
def ua_graph_data_path():
    return get_project_root() / "tests" / "testdata" / "ua_graph_functions"


@pytest.fixture
def ua_object_node_row() -> pd.Series:
    return pd.Series(
        {
            "NodeClass": "UAObject",
            "DisplayName": "Site1",
            "Description": "Lorem ipsum dolor sit amet",
            "Value": pd.NA,
            "NodeId": "ns=1;i=1",
            "BrowseName": "Site1",
            "SymbolicName": pd.NA,
            "IsAbstract": pd.NA,
            "Symmetric": pd.NA,
            "ValueRank": pd.NA,
            "ArrayDimensions": pd.NA,
            "MinimumSamplingInterval": pd.NA,
            "AccessLevel": pd.NA,
            "EventNotifier": pd.NA,
            "BrowseNameNamespace": 1,
            "ns": 1,
            "id": 3909,
            "ParentNodeId": pd.NA,
            "DataType": pd.NA,
            "MethodDeclarationId": pd.NA,
        }
    )


@pytest.fixture
def ua_variable_node_row() -> pd.Series:
    return pd.Series(
        {
            "NodeClass": "UAVariable",
            "DisplayName": "EURange",
            "Description": "",
            "Value": UAEURange(low=2.2, high=1984.2),
            "NodeId": "ns=1;i=40",
            "BrowseName": "EURange",
            "SymbolicName": pd.NA,
            "IsAbstract": pd.NA,
            "Symmetric": pd.NA,
            "ValueRank": pd.NA,
            "ArrayDimensions": pd.NA,
            "MinimumSamplingInterval": pd.NA,
            "AccessLevel": "3",
            "EventNotifier": pd.NA,
            "BrowseNameNamespace": 0,
            "ns": 1,
            "id": 3916,
            "ParentNodeId": pd.NA,
            "DataType": UANodeId(
                namespace=0, nodeid_type=NodeIdType.NUMERIC, value="884"
            ),
            "MethodDeclarationId": pd.NA,
            "IsValidValue": True,
        }
    )

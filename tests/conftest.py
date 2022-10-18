import pytest
from definitions import get_project_root


@pytest.fixture(scope="session")
def paper_example_path():
    return get_project_root() / "tests" / "testdata" / "paper_example"


@pytest.fixture(scope="session")
def ua_graph_data_path():
    return get_project_root() / "tests" / "testdata" / "ua_graph_functions"

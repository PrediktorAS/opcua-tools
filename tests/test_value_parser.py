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

from opcua_tools.value_parser import parse_boolean
import pytest
import pandas as pd


@pytest.fixture(scope="session")
def test_data():
    list = [
        ["Boolean", "false", False],
        ["Boolean", "False", False],
        ["Boolean", "true", True],
        ["Boolean", "True", True],
    ]
    data = pd.DataFrame(list, columns=["tag_type", "input", "solution"])
    return data


def test_parse_boolean(test_data):
    """Ensuring that the parse_boolean function in value_parser.py
    will properly deal with upper and lower case representations of
    strings in python."""

    data = test_data.copy()
    data["dataclass"] = data["input"].apply(lambda value: parse_boolean(value))
    data["output"] = data["dataclass"].apply(lambda bool_class: bool_class.value)
    pd.testing.assert_series_equal(data["output"], data["solution"], check_names=False)

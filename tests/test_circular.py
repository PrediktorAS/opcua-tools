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

from opcua_tools.nodeset_parser import (
    exclude_files_not_in_namespaces,
    get_list_of_xml_files,
    get_xml_namespaces,
)
import opcua_tools as ot
import os
import pandas as pd
from pathlib import Path
from definitions import get_project_root

PATH_HERE = os.path.dirname(__file__)


def test_find_circular_reference_nodes():
    namespace_dict = {
        0: "http://opcfoundation.org/UA/",
        1: "http://test.org/Circular/",
    }
    xml_directory = str(get_project_root() / "tests" / "testdata" / "circular")
    uag = ot.UAGraph.from_path(xml_directory, namespace_dict)
    crn = uag.find_circular_reference_nodes("http://test.org/Circular/")
    assert str(crn['NodeId'].values[0]) == 'ns=1;i=5003'
    assert str(crn['NodeId'].values[1]) == 'ns=1;i=5005'
    assert str(crn['NodeId'].values[2]) == 'ns=1;i=5004'
    assert str(crn['NodeId'].values[3]) == 'ns=1;i=5006'


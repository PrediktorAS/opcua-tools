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

import opcua_tools as ot
import os
PATH_HERE = os.path.dirname(__file__)


def test_parsing_without_errors():
    ot.parse_xml_dir(PATH_HERE + '/testdata/parser')

def test_parse_nodeid():
    s = 'ns=1;i=0'
    nid = ot.parse_nodeid(s)

    assert type(nid.value) == int
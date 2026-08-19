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
import lxml.etree as ET

SECURE_XML_PARSER_DEFAULTS = {
    "resolve_entities": False,
    "no_network": True,
    "dtd_validation": False,
    "load_dtd": False,
    "huge_tree": False,
}


def secure_xml_parser(**kwargs) -> ET.XMLParser:
    merged_kwargs = {**SECURE_XML_PARSER_DEFAULTS, **kwargs}
    return ET.XMLParser(**merged_kwargs)

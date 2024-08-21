import json
from typing import List

import lxml.etree as ET

from opcua_tools.json_parser.type_hints import (
    AliasesLine,
    ModelLine,
    ModelsLine,
    NameSpaceURIsLine,
    RequiredModelLine,
    UANodeSetLine,
)
from opcua_tools.ua_data_types import UANodeId
from opcua_tools.value_parser import parse_nodeid


def pre_process_xml_to_json(file_path):
    """
    Creates a JSON file which should have the same data as this XML file
    but in a more easily digestable format (JSONL).
    The goal is to separate the pre-processing of XML files (convert to processed JSON)
    from processing the data in XML files. This function is the pre-processing step.
    The pre-processing is very opinionated: each JSON line is formatted, so the next step
    which reads these JSON files can do it while using little memory and CPU time.
    """
    output_file_name = f"{file_path}_parsed.json"

    uanodeset_tag = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}UANodeSet"
    namespace_uris_tag = (
        "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}NamespaceUris"
    )
    uri_tag = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Uri"
    models_tag = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Models"
    model_tag = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Model"
    required_model_tag = (
        "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}RequiredModel"
    )
    aliases_tag = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Aliases"
    alias_tag = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Alias"

    tree = ET.parse(file_path)
    root = tree.getroot()

    with open(output_file_name, "w") as f:
        root_iter = root.iter()
        for elem in root_iter:
            if elem.tag == uanodeset_tag:
                line: UANodeSetLine = {"elem_type": "UANodeSet", "tag": uanodeset_tag}
                f.write(json.dumps(line) + "\n")
            elif elem.tag == namespace_uris_tag:
                line: NameSpaceURIsLine = {
                    "elem_type": "NamespaceUris",
                    "uris": [uri_elem.text for uri_elem in elem],
                }
                f.write(json.dumps(line) + "\n")
            elif elem.tag == model_tag:
                pass
            elif elem.tag == required_model_tag:
                pass
            elif elem.tag == uri_tag:
                pass
            elif elem.tag == models_tag:
                models: List[ModelLine] = []
                for model in elem:
                    req_models: List[RequiredModelLine] = []
                    for req_model in model.iterchildren():
                        req_models.append(
                            {
                                "uri": req_model.get("ModelUri"),
                                "publication_date": req_model.get("PublicationDate"),
                                "version": req_model.get("Version"),
                            }
                        )
                    models.append(
                        {
                            "uri": model.get("ModelUri"),
                            "publication_date": model.get("PublicationDate"),
                            "version": model.get("Version"),
                            "required_models": req_models,
                        }
                    )
                line: ModelsLine = {
                    "elem_type": "Models",
                    "uris": [model.get("ModelUri") for model in elem],
                    "models": models,
                }
                f.write(json.dumps(line) + "\n")
            elif elem.tag == alias_tag:
                pass
            elif elem.tag == aliases_tag:
                aliases = list()
                line: AliasesLine = {"elem_type": "Aliases", "aliases": aliases}
                for alias in elem:
                    res: UANodeId = parse_nodeid(alias.text)
                    aliases.append(
                        {
                            "name": alias.attrib["Alias"],
                            "nodeid": {
                                "namespace": res.namespace,
                                "type": res.nodeid_type.value,
                                "value": res.value,
                            },
                        }
                    )
                f.write(json.dumps(line) + "\n")
            else:
                break

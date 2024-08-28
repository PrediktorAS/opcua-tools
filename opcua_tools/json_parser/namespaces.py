import json
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

OPCFOUNDATION_NAMESPACE = "http://opcfoundation.org/UA/"


def get_namespace_data_from_file(json_file_path: str) -> dict:
    """
    Get namespace data from JSON file
    Args:
        xml_file (str): The full filepath to the xml file to check

    Returns:
        A dictionary containing file namespace name and a list of required namespaces
        Example:
            {
                "name": "http://powerview.com/enterprise",
                "included_namespaces": {
                    "http://prediktor.no/PVTypes/",
                    "http://opcfoundation.org/UA/",
                }
            }
    """
    if not json_file_path.endswith("_parsed.json"):
        json_file_path += "_parsed.json"
    # In some NodeSet2 definition files the <Model> tag is not found
    # therefore using the common files name as well.
    opcua_namespace_data = {
        "name": OPCFOUNDATION_NAMESPACE,
        "included_namespaces": set(),
    }
    if json_file_path.endswith("Opc.Ua.NodeSet2.xml_parsed.json"):
        return opcua_namespace_data

    namespace_data = None
    namespace_uris_line = None

    with open(json_file_path, "r") as f:
        for line in f.readlines():
            line = json.loads(line)
            namespace_data = None
            if line["elem_type"] == "Models":
                for model_uri in line["uris"]:
                    if model_uri == OPCFOUNDATION_NAMESPACE:
                        namespace_data = opcua_namespace_data
                    else:
                        namespace_data = {
                            "name": model_uri,
                            "included_namespaces": {OPCFOUNDATION_NAMESPACE},
                        }
                    break  # get just the first Model tag (there should be no more Model tags)

            if namespace_data is not None:
                break

            if line["elem_type"] == "NamespaceUris":
                namespace_uris_line = line
                continue

    if namespace_data is None:
        message = f"Missing 'Model' tag in {json_file_path}"
        logger.error(message)
        raise ValueError(message)

    if namespace_uris_line is None:
        if namespace_data["name"] == OPCFOUNDATION_NAMESPACE:
            return namespace_data
        else:
            message = f"Missing 'NamespaceUris' tag in {json_file_path}"
            logger.error(message)
            raise ValueError(message)

    for namespace_uri_tag in namespace_uris_line["uris"]:
        if namespace_uri_tag != namespace_data["name"]:
            namespace_data["included_namespaces"].add(namespace_uri_tag)

    return namespace_data

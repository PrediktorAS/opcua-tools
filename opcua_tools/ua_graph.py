import gc
import logging
from datetime import datetime
from io import StringIO
from typing import Dict, List, Optional, Union

import pandas as pd

import opcua_tools.nodes_manipulation as nodes_manipulation
from opcua_tools import memory_optimizer
from opcua_tools.navigation import (
    fast_transitive_closure,
    find_relatives,
    hierarchical_references,
    resolve_ids_from_browsenames,
)
from opcua_tools.nodeset_generator import (
    create_lookup_df,
    create_nodeset2_file,
    denormalize_nodes_nodeids,
    denormalize_references_nodeids,
)
from opcua_tools.nodeset_parser import parse_xml_dir, parse_xml_files
from opcua_tools.ua_data_types import UANodeId

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
memory_optimizer.replace_default_pandas_del_method()


class UAGraph:
    def __init__(
        self,
        nodes: pd.DataFrame,
        references: pd.DataFrame,
        namespaces: list[str],
        models: list[dict],
    ):
        self.nodes = nodes
        self.nodes["id"] = self.nodes["id"].astype(pd.Int32Dtype())
        self.references = references
        self.references["Src"] = self.references["Src"].astype(pd.Int32Dtype())
        self.references["Trg"] = self.references["Trg"].astype(pd.Int32Dtype())
        self.references["ReferenceType"] = self.references["ReferenceType"].astype(
            pd.Int32Dtype()
        )
        self.namespaces = namespaces
        self.models = models

    @classmethod
    def from_path(
        cls, path: str, namespace_dict: Optional[Dict[int, str]] = None
    ) -> "UAGraph":
        if namespace_dict:
            namespace_list = UAGraph._get_namespace_list(namespace_dict)
            parse_dict = parse_xml_dir(path, namespace_list)
        else:
            parse_dict = parse_xml_dir(path)

        nodes = parse_dict["nodes"]
        references = parse_dict["references"]

        cls.__validate_referenced_nodes_exists(nodes, references)

        ua_graph = cls(
            nodes=nodes,
            references=references,
            namespaces=parse_dict["namespaces"],
            models=parse_dict["models"],
        )

        del parse_dict["nodes"]
        del parse_dict["references"]
        gc.collect()

        nodes_manipulation.transform_ints_to_enums(ua_graph)

        return ua_graph

    @classmethod
    def from_file_list(
        cls, file_list: List[str], namespace_dict: Optional[Dict[int, str]] = None
    ) -> "UAGraph":
        if namespace_dict:
            namespace_list = UAGraph._get_namespace_list(namespace_dict)
            parse_dict = parse_xml_files(file_list, namespace_list)
        else:
            parse_dict = parse_xml_files(file_list)

        nodes = parse_dict["nodes"]
        references = parse_dict["references"]

        cls.__validate_referenced_nodes_exists(nodes, references)

        del parse_dict["nodes"]
        del parse_dict["references"]
        gc.collect()

        return cls(
            nodes=nodes,
            references=references,
            namespaces=parse_dict["namespaces"],
            models=parse_dict["models"],
        )

    @staticmethod
    def _get_namespace_list(namespace_dict: dict) -> list:
        namespace_list = []
        max_namespace = max(namespace_dict.keys()) + 1
        for namespace_index in range(0, max_namespace):
            if namespace_index in namespace_dict.keys():
                namespace_list.append(namespace_dict[namespace_index])
            else:
                namespace_list.append("None")
        return namespace_list

    @staticmethod
    def __validate_referenced_nodes_exists(
        nodes_df: pd.DataFrame, references_df: pd.DataFrame
    ) -> None:
        node_ids = set(nodes_df["id"])

        if not (source_refs_set := set(references_df["Src"])).issubset(node_ids):
            diff = source_refs_set - node_ids
            raise ValueError(f"Some SourceIds or SourceKeys do not exist: {diff}")

        if not (target_refs_set := set(references_df["Trg"])).issubset(node_ids):
            diff = target_refs_set - node_ids
            raise ValueError(f"Some TargetIds or TargetKeys do not exist: {diff}")

    def all_references_of_type(self, browsename: str):
        return self.references[
            self.references["ReferenceType"]
            == self.reference_type_by_browsename(browsename)
        ].copy()

    def __ua_nodeclass_by_browsename(
        self, browsename: str, nodeclass: Optional[str] = None
    ) -> int:
        """Retrieves the internal id from the OPC UA graph which has a NodeClass `nodeclass`
        (UAVariableType in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised.

        Args:
            browsename (str): BrowseName of the node to find.
            nodeclass (Optional[str], optional): NodeClass of the node to find. Defaults to None.

        Raises:
            ValueError: If browsename is None or empty string.
            ValueError: If no node is found.
            ValueError: If multiple nodes are found.

        Returns:
            int: The internal id of the node.
        """
        if browsename is None or browsename == "":
            raise ValueError(
                f'"browsename" must not be None or empty string, should be BrowseName of {nodeclass}'
            )

        if nodeclass:
            nodeclass_nodes = self.nodes[self.nodes["NodeClass"] == f"UA{nodeclass}"]
        else:
            nodeclass_nodes = self.nodes

        nodeclass_ids = resolve_ids_from_browsenames(
            nodes=nodeclass_nodes, browsenames=[browsename]
        )
        if len(nodeclass_ids) == 0:
            raise ValueError(f"Could not find {nodeclass} " + browsename)
        elif len(nodeclass_ids) > 1:
            raise ValueError(f"Multiple hits for {nodeclass} " + browsename + " found.")
        else:
            nodeclass_id = nodeclass_ids.iloc[0]
        return int(nodeclass_id)

    def reference_type_by_browsename(self, browsename: str) -> int:
        """Retrieves the internal id from the OPC UA graph which has a NodeClass "ReferenceType"
        (UAReferenceType in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised.

        Args:
            browsename (str): BrowseName of the node to find.

        Returns:
            int: The internal id of the node.
        """
        return self.__ua_nodeclass_by_browsename(browsename, "ReferenceType")

    def object_type_by_browsename(self, browsename: str) -> int:
        """Retrieves the internal id from the OPC UA graph which has a NodeClass "ObjectType"
        (UAObjectType in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised.

        Args:
            browsename (str): BrowseName of the node to find.

        Returns:
            int: The internal id of the node.
        """
        return self.__ua_nodeclass_by_browsename(browsename, "ObjectType")

    def variable_type_by_browsename(self, browsename: str) -> int:
        """Retrieves the internal id from the OPC UA graph which has a NodeClass "VariableType"
        (UAVariableType in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised.

        Args:
            browsename (str): BrowseName of the node to find.

        Returns:
            int: The internal id of the node.
        """
        return self.__ua_nodeclass_by_browsename(browsename, "VariableType")

    def data_type_by_browsename(self, browsename: str) -> int:
        """Retrieves the internal id from the OPC UA graph which has a NodeClass "DataType"
        (UADataType in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised.

        Args:
            browsename (str): BrowseName of the node to find.

        Returns:
            int: The internal id of the node.
        """
        return self.__ua_nodeclass_by_browsename(browsename, "DataType")

    def object_by_browsename(self, browsename: str) -> int:
        """Retrieves the internal id from the OPC UA graph which has a NodeClass "Object"
        (UAObject in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised.

        Args:
            browsename (str): BrowseName of the node to find.

        Returns:
            int: The internal id of the node.
        """
        return self.__ua_nodeclass_by_browsename(browsename, "Object")

    def nodeid_by_browsename(
        self, browsename: str, nodeclass: Optional[str] = None
    ) -> int:
        """Retrieves the NodeId from the OPC UA graph which has a NodeClass `nodeclass`
        (UAVariableType in the UAGraph), for the given `browsename` input. If multiple nodes
        are found, an error is raised. Please note that the 'nodeclass' variable has to be
        a string, e.g. "VariableType", "DataType", etc. in the form of CamelCase.

        Args:
            browsename (str): BrowseName of the node to find.
            nodeclass (Optional[str], optional): NodeClass of the node to find. Defaults to None.

        Raises:
            ValueError: If browsename is None or empty string.
            ValueError: If no node is found.
            ValueError: If multiple nodes are found.

        Returns:
            int: The NodeId of the node.
        """
        if nodeclass:
            id = self.__ua_nodeclass_by_browsename(browsename, nodeclass)
        else:
            id = self.__ua_nodeclass_by_browsename(browsename)

        if id is None:
            raise ValueError(f"Could not find node with browsename {browsename}")
        node_id = self.nodes.loc[self.nodes["id"] == id, "NodeId"].values[0]
        return node_id

    def write_nodeset(
        self,
        filename_or_stringio: Union[str, StringIO],
        namespace_uri: str,
        include_outgoing_instance_level_references: Optional[bool] = True,
        last_modified: Optional[datetime] = None,
        publication_date: Optional[datetime] = None,
        new_model_version: Optional[str] = None,
    ):
        if namespace_uri not in self.namespaces:
            raise ValueError("Could not find namespace uri: " + namespace_uri)
        namespace_index = self.namespaces.index(namespace_uri)
        if not include_outgoing_instance_level_references:
            use_references = self.remove_instance_level_outgoing_references(
                namespace_index=namespace_index
            )
        else:
            use_references = self.references

        # Always serialize namespace 1 in xml, so we need to remap indices
        new_namespaces_list = [self.namespaces[0], self.namespaces[namespace_index]]
        for i, n in enumerate(self.namespaces):
            if i != 0 and i != namespace_index:
                new_namespaces_list.append(n)

        remapper = {
            i: new_namespaces_list.index(n) for i, n in enumerate(self.namespaces)
        }
        use_nodes = self.nodes.copy()
        use_nodes["BrowseNameNamespace"] = use_nodes["BrowseNameNamespace"].astype(
            pd.Int32Dtype()
        )
        use_nodes["NodeId"] = use_nodes["NodeId"].map(
            lambda x: UANodeId(
                namespace=remapper[x.namespace],
                value=x.value,
                nodeid_type=x.nodeid_type,
            )
        )
        use_nodes["BrowseNameNamespace"] = use_nodes["BrowseNameNamespace"].map(
            remapper
        )

        create_nodeset2_file(
            nodes=use_nodes,
            references=use_references,
            models=self.models,
            serialize_namespace=1,
            namespaces=new_namespaces_list,
            filename_or_stringio=filename_or_stringio,
            last_modified=last_modified,
            publication_date=publication_date,
            new_model_version=new_model_version,
        )

    def get_normalized_nodes_df(self, namespace_uri: Optional[str] = None):
        lookup_df = create_lookup_df(self.nodes)
        if namespace_uri is not None:
            ns = self.namespaces.index(namespace_uri)
            nodes = self.nodes[self.nodes["ns"] == ns].copy()
        else:
            nodes = self.nodes.copy()
        nodes = denormalize_nodes_nodeids(nodes, lookup_df)
        nodes = nodes.drop(columns=["id"])
        nodes = nodes.sort_values(by=nodes.columns.values.tolist(), ignore_index=True)
        return nodes

    def __get_references_df(self, namespace_uri: str):
        ns = self.namespaces.index(namespace_uri)
        nodes_ns = self.nodes.loc[self.nodes["ns"] == ns, ["id"]].set_index("id")
        nodes_ns["in_ns"] = True
        references = (
            self.references.set_index("Src", drop=False)
            .join(nodes_ns)
            .rename(columns={"in_ns": "src_in_ns"}, errors="raise")
        )
        references = (
            references.set_index("Trg", drop=False)
            .join(nodes_ns)
            .rename(columns={"in_ns": "trg_in_ns"}, errors="raise")
        )
        references = references.loc[
            (references["src_in_ns"] == True) | (references["trg_in_ns"] == True),
            ["Src", "Trg", "ReferenceType"],
        ].copy()
        return references

    def get_normalized_references_df(self, namespace_uri: Optional[str] = None):
        lookup_df = create_lookup_df(self.nodes)
        if namespace_uri is not None:
            references = self.__get_references_df(namespace_uri)
        else:
            references = self.references.copy()

        references = denormalize_references_nodeids(references, lookup_df)
        references = references.sort_values(
            by=references.columns.values.tolist(), ignore_index=True
        )
        return references

    def remove_instance_level_outgoing_references(
        self, namespace_index: int
    ) -> pd.DataFrame:
        hmr = self.reference_type_by_browsename("HasModellingRule")
        htd = self.reference_type_by_browsename("HasTypeDefinition")
        self.nodes["ns"] = self.nodes["NodeId"].map(lambda x: x.namespace)
        ids_in_ns = self.nodes.loc[self.nodes["ns"] == namespace_index, ["id"]].copy()
        ids_in_ns = ids_in_ns.set_index("id", drop=False)

        references = self.references.set_index("Trg", drop=False)

        references = references[
            references.index.isin(ids_in_ns.index)
            | (references["ReferenceType"] == hmr)
            | (references["ReferenceType"] == htd)
        ].copy()

        return references

    def get_browsenames_for_nodeclass(
        self, node_class: str, namespace: Optional[int] = None
    ) -> List[str]:
        """This function will provide the option of returning the list of references
        present in the graph. The number of the namespace in which the reference type
        is defined can be specified to further narrow the search. If none is provided
        it will return all namespaces"""

        object_type_nodes = self.nodes[self.nodes["NodeClass"] == node_class]

        if namespace is not None:
            object_type_nodes.reset_index(inplace=True)
            mask = object_type_nodes["NodeId"].map(lambda x: x.namespace) == namespace
            object_type_nodes = object_type_nodes[mask]

        return object_type_nodes["BrowseName"].unique().tolist()

    def _get_browsename_from_id(self, id: int) -> str:
        row = self.nodes[self.nodes["id"] == id]
        return row["BrowseName"].values[0]

    def get_nodes_classes(self):
        return self.nodes["NodeClass"].unique().tolist()

    def get_instances_with_type_info(self):
        """Returns the UAObjects and the browsename of their type"""
        nodes = self.nodes[["NodeClass", "BrowseName", "NodeId", "id"]].set_index(
            "id", drop=False
        )
        has_type_def_id = self.reference_type_by_browsename("HasTypeDefinition")
        references_with_htd_id = self.references.loc[
            self.references["ReferenceType"] == has_type_def_id
        ]
        references_with_htd_id = references_with_htd_id[["Src", "Trg"]]
        typeinfo = nodes.rename(
            columns={
                "BrowseName": "TypeBrowseName",
                "NodeId": "TypeNodeId",
                "id": "Typeid",
            },
            errors="raise",
        ).drop(columns=["NodeClass"])
        references_with_nodes = (
            references_with_htd_id.set_index("Src")
            .join(nodes)
            .set_index("Trg")
            .join(typeinfo)
        )
        return references_with_nodes

    def get_enum_dict(self, enum_name: str):
        """This function will return the enum given its name in
        the form of a dict."""

        enum_node = self.nodes[
            (self.nodes.NodeClass == "UADataType")
            & (self.nodes.BrowseName == enum_name)
        ]

        if enum_node.shape[0] == 0:
            raise ValueError("The enum was not found in the graph")

        if enum_node.shape[0] > 1:
            raise ValueError("The enum was found multiple times in the graph")

        has_property_id = self.reference_type_by_browsename("HasProperty")
        node_id = enum_node["id"].values[0]
        outgoing_reference_row = self.references[
            (self.references.ReferenceType == has_property_id)
            & (self.references.Src == node_id)
        ]
        outgoing_id = outgoing_reference_row["Trg"].values[0]
        has_property_node = self.nodes[self.nodes["id"] == outgoing_id]
        has_property_name = has_property_node["BrowseName"].values[0]
        enumeration_datatypes = ["EnumStrings", "EnumValues"]
        if has_property_name not in enumeration_datatypes:
            raise ValueError(
                "The ReferenceType associated with the enum_name is not an EnumStrings or EnumValues"
            )

        enum_dict = dict()

        if has_property_name == "EnumStrings":
            ua_list_of = has_property_node["Value"].values[0]
            for localized_text_i, localized_text in enumerate(ua_list_of.value):
                # For case insensitivity captializing first word if string
                if isinstance(localized_text.text, str):
                    enum_dict[localized_text_i] = localized_text.text.title()
                else:
                    enum_dict[localized_text_i] = localized_text.text
        else:
            raise NotImplementedError("EnumValues not implemented")

        return enum_dict

    def get_enum_string(self, enum_name: str, number: int):
        """This function will return the string value of within an enum,
        provided you get both the of the enum and an integer value."""
        enum_dict = self.get_enum_dict(enum_name)
        # TODO: Cache enumdict for performance
        return enum_dict[number]

    def get_enum_int(self, enum_name: str, string: str):
        """This function will return the integer value of within an enum,
        provided you get both the of the enum and a string value."""
        # Ad Hoc solution to ensure text in files does not include newlines and line breaks
        string = string.replace("\r", "")
        string = string.replace("\n", "")
        string = string.title()
        string = string.strip()
        enum_dict = self.get_enum_dict(enum_name)
        # TODO: Cache enumdict for performance
        # Getting the dict key based on the value
        key_list = list(enum_dict.keys())
        val_list = list(enum_dict.values())
        try:
            position = val_list.index(string)
            return key_list[position]
        except Exception as get_enum_int_error:
            raise ValueError(
                "Could not find the string: {}, for the enum_name: {}".format(
                    string, enum_name
                )
            ) from get_enum_int_error

    def get_objects_of_type(self, type_name: str):
        has_type_def = self.reference_type_by_browsename("HasTypeDefinition")
        object_type_df = self.object_type_by_browsename(type_name)
        reference_ids = self.references[
            (self.references["ReferenceType"] == has_type_def)
            & (self.references["Trg"] == object_type_df)
        ]
        return self.nodes.loc[self.nodes["id"].isin(reference_ids["Src"])]

    def get_neighboring_nodes_by_browsename(
        self, browse_name: str, node_type: str, relation: str
    ):
        """This function will returning the references either pointing to
        or from a node. The results contain the source and target contents of
        the `references` table with actual text 'BrowseNames' and the corresponding
        node 'NodeIdes'. The 'relation' parameter is special since it must
        either be "outgoing" or "incoming". When inputting "child" it will return
        the outgoing references of the node, while "parent" will provide the
        references which point to the specific node."""

        id = None
        if node_type == "UAObject":
            id = self.object_by_browsename(browse_name)
        elif node_type == "UADataType":
            id = self.data_type_by_browsename(browse_name)
        elif node_type == "UAReferenceType":
            id = self.reference_type_by_browsename(browse_name)
        elif node_type == "UAObjectType":
            id = self.object_type_by_browsename(browse_name)
        elif node_type == "UAVariableType":
            id = self.variable_type_by_browsename(browse_name)
        else:
            raise ValueError(
                f"node_type, {node_type}, is not one of the proper types: "
                f"UAObject, UADataType, UAReferenceType, UAObjectType, UAVariableType"
            )

        if not id:
            raise ValueError(f"The id was not properly set and is {id}")

        return self.get_neighboring_nodes_by_id(id, relation)

    def get_neighboring_nodes_by_id(self, id: int, relation: str):

        direction = None
        if relation == "outgoing":
            direction = "Src"
        elif relation == "incoming":
            direction = "Trg"

        if direction == None:
            raise ValueError(
                "The relation of the neighbouring nodes must be"
                + 'indicated by setting "relation" to either "outgoing" or "incoming".'
            )

        # Creating duplicate for safety's sake
        references = self.references.copy()

        # Getting getting the subset of references which only contain the desired node
        references = references[references[direction] == id]

        # Creating a dataframe with only names to conduct joins and get names
        names = self.nodes[["BrowseName", "NodeId", "id"]].set_index("id", drop=True)

        # Getting the names of the ReferenceTypes into the tables instead of numbers
        references.set_index("ReferenceType", drop=True, inplace=True)
        references = references.join(names, how="inner")
        references.rename(columns={"BrowseName": "ReferenceType"}, inplace=True)
        references.drop("NodeId", axis=1, inplace=True)

        # Getting names of the ids in the Src Column, joining in the same manner as before
        references.set_index("Src", drop=False, inplace=True)
        references = references.join(names, how="inner")
        references.rename(
            columns={"BrowseName": "Source", "NodeId": "SourceNodeId"}, inplace=True
        )

        # Getting names of the ids in the Trg Column, joining in the same manner as before
        references.set_index("Trg", drop=False, inplace=True)
        references = references.join(names, how="inner")
        references.rename(
            columns={"BrowseName": "Target", "NodeId": "TargetNodeId"}, inplace=True
        )

        return references

    def create_node_paths_by_reference_types(
        self,
        root_node_browsename: str,
        hierarchical_reference_types: List[str],
    ) -> pd.DataFrame:
        root_node_id = self.object_by_browsename(root_node_browsename)

        reference_type_ids = []
        for ref in hierarchical_reference_types:
            try:
                reference_type_ids.append(self.reference_type_by_browsename(ref))
            except IndexError as e:
                logger.error(
                    f"The ReferenceType: {ref}, was not found in the nodes and references"
                )
                raise

        hierarchical_references = self.references[
            self.references["ReferenceType"].isin(reference_type_ids)
        ]
        root_node_id_df = self.nodes.loc[
            self.nodes["id"] == root_node_id, ["id"]
        ].copy()
        relatives = find_relatives(
            nodes=root_node_id_df,
            nodes_key_col="id",
            edges=hierarchical_references,
            relative_type="d",
            keep_paths=True,
        )

        path_columns = [c for c in relatives.columns if type(c) == int and c > 0]

        relatives = (
            relatives.drop("id", axis=1)
            .melt(id_vars=[0, "end"], value_vars=path_columns, value_name="id")
            .dropna()
        )
        nodes_browsename = self.nodes[["id", "BrowseName"]].set_index("id")

        relatives = (
            relatives.set_index("id").join(nodes_browsename).reset_index(drop=True)
        )
        relatives = relatives.sort_values(by=[0, "end", "variable"], ignore_index=True)
        relatives = relatives.rename(columns={0: "start"})
        relatives = (
            relatives.groupby(by=["start", "end"])
            .agg({"BrowseName": lambda x: "/".join(x.to_list())})
            .reset_index()
        )

        node_paths = relatives[["end", "BrowseName"]].rename(
            columns={"end": "id", "BrowseName": "NodePath"}
        )
        root_node_id_df_to_add = pd.DataFrame({"id": [root_node_id], "NodePath": [""]})
        node_paths = pd.concat([node_paths, root_node_id_df_to_add])

        # Adding the root_node to the start of the path
        node_paths["NodePath"] = node_paths["NodePath"].apply(
            lambda name: "/".join([root_node_browsename, name])
        )
        node_paths = node_paths.sort_values("NodePath").reset_index(drop=True)

        return node_paths

    def find_circular_reference_nodes(self, namespace_uri: str) -> pd.DataFrame:
        """This function finds circular references in the given namespace. Returns a dataframe with the Node IDs involved in the circular references"""
        lookup_df = create_lookup_df(self.nodes)
        refs_ns = self.__get_references_df(namespace_uri)
        type_references = self.references
        type_nodes = self.nodes
        hierarchy_refs = hierarchical_references(refs_ns, type_references, type_nodes)
        transitive_closures = fast_transitive_closure(hierarchy_refs)
        cyclic_refs = pd.merge(
            transitive_closures,
            transitive_closures,
            how="inner",
            left_on=["Src", "Trg"],
            right_on=["Trg", "Src"],
        )
        cyclic_refs = pd.DataFrame(cyclic_refs["Src_x"].unique(), columns=["Src"])
        refcols = ["Src"]
        for col in refcols:
            uniques = lookup_df.rename(columns={"uniques": col}, errors="raise")
            cyclic_refs = (
                cyclic_refs.set_index(col).join(uniques).reset_index(drop=True)
            )
        cyclic_refs = cyclic_refs.rename(columns={"Src": "NodeId"})
        return cyclic_refs

    def __get_nodes_from_ns(self, namespace_uri: str):
        ns = self.namespaces.index(namespace_uri)
        nodes_ns = self.nodes.loc[self.nodes["ns"] == ns, ["id"]].set_index("id")
        return nodes_ns

import pandas as pd
from .nodeset_parser import parse_xml_dir
from .navigation import resolve_ids_from_browsenames
from .nodeset_generator import create_nodeset2_file
from typing import List, Optional, Union
from io import StringIO

class UAGraph:
    def __init__(self, nodes:pd.DataFrame, references:pd.DataFrame, namespaces:List[str]):
        self.nodes = nodes
        self.nodes['id'] = self.nodes['id'].astype(pd.Int32Dtype())
        self.references = references
        self.references['Src'] = self.references['Src'].astype(pd.Int32Dtype())
        self.references['Trg'] = self.references['Trg'].astype(pd.Int32Dtype())
        self.references['ReferenceType'] = self.references['ReferenceType'].astype(pd.Int32Dtype())
        self.namespaces = namespaces

    def from_path(path:str) -> 'UAGraph':
        parse_dict = parse_xml_dir(path)
        return UAGraph(nodes=parse_dict['nodes'],
                             references=parse_dict['references'],
                             namespaces=parse_dict['namespaces'])

    def reference_type_by_browsename(self, browsename:str) -> int:
        if browsename is None or browsename == '':
            raise ValueError('"browsename" must not be None or empty string, should be BrowseName of ReferenceType')

        reference_type_nodes = self.nodes[self.nodes['NodeClass'] == 'UAReferenceType']
        reference_type_ids = resolve_ids_from_browsenames(nodes=reference_type_nodes, browsenames=[browsename])
        if len(reference_type_ids) == 0:
            raise ValueError('Could not find ReferenceType ' + browsename)
        elif len(reference_type_ids) > 1:
            raise ValueError('Multiple hits for ReferenceType ' + browsename + ' please specify namespace')
        else:
            reference_type_id = reference_type_ids.iloc[0]

        return int(reference_type_id)


    def object_type_by_browsename(self, browsename: str) -> int:
        if browsename is None or browsename == '':
            raise ValueError('"browsename" must not be None or empty string, should be BrowseName of ObjectType')

        object_type_nodes = self.nodes[self.nodes['NodeClass'] == 'UAObjectType']
        object_type_ids = resolve_ids_from_browsenames(nodes=object_type_nodes, browsenames=[browsename])
        if len(object_type_ids) == 0:
            raise ValueError('Could not find object type ' + browsename)
        elif len(object_type_ids) > 1:
            raise ValueError('Multiple hits for object type ' + browsename + ' please specify namespace')
        else:
            object_type_id = object_type_ids.iloc[0]

        return int(object_type_id)


    def data_type_by_browsename(self, browsename: str) -> int:
        if browsename is None or browsename == '':
            raise ValueError('"browsename" must not be None or empty string, should be BrowseName of DataType')

        data_type_nodes = self.nodes[self.nodes['NodeClass'] == 'UADataType']
        data_type_ids = resolve_ids_from_browsenames(nodes=data_type_nodes, browsenames=[browsename])
        if len(data_type_ids) == 0:
            raise ValueError('Could not find data type ' + browsename)
        elif len(data_type_ids) > 1:
            raise ValueError('Multiple hits for data type ' + browsename + ' please specify namespace')
        else:
            data_type_id = data_type_ids.iloc[0]

        return int(data_type_id)

    def object_by_browsename(self, browsename: str) -> int:
        if browsename is None or browsename == '':
            raise ValueError('"browsename" must not be None or empty string, should be BrowseName of Object')

        object_nodes = self.nodes[self.nodes['NodeClass'] == 'UAObject']
        object_ids = resolve_ids_from_browsenames(nodes=object_nodes, browsenames=[browsename])
        if len(object_ids) == 0:
            raise ValueError('Could not find object ' + browsename)
        elif len(object_ids) > 1:
            raise ValueError('Multiple hits for object ' + browsename + ' please specify namespace')
        else:
            reference_type_id = object_ids.iloc[0]

        return int(reference_type_id)

    def write_nodeset(self, filename_or_stringio:Union[str, StringIO], namespace_uri:str,
                      include_outgoing_instance_level_references:Optional[bool] = True):
        if namespace_uri not in self.namespaces:
            raise ValueError('Could not find namespace uri: ' + namespace_uri)
        namespace_index = self.namespaces.index(namespace_uri)
        if not include_outgoing_instance_level_references:
            use_references = self.remove_instance_level_outgoing_references(namespace_index=namespace_index)
        else:
            use_references = self.references

        create_nodeset2_file(nodes=self.nodes,
                             references=use_references,
                             serialize_namespace=namespace_index,
                             namespaces=self.namespaces,
                             filename_or_stringio=filename_or_stringio)

    def remove_instance_level_outgoing_references(self, namespace_index:int) -> pd.DataFrame:
        hmr = self.reference_type_by_browsename('HasModellingRule')
        htd = self.reference_type_by_browsename('HasTypeDefinition')
        self.nodes['ns'] = self.nodes['NodeId'].map(lambda x:x.namespace)
        ids_in_ns = self.nodes.loc[self.nodes['ns'] == namespace_index, ['id']].copy()
        ids_in_ns = ids_in_ns.set_index('id', drop=False)

        references = self.references.set_index('Trg', drop=False)

        references = references[references.index.isin(ids_in_ns.index) |
                                (references['ReferenceType'] == hmr) |
                                (references['ReferenceType'] == htd)].copy()

        return references

    def get_browsenames_for_nodeclass(self, node_class: str, namespace: Optional[int] = None) -> List[str]:
        """This function will provide the option of returning the list of references
        present in the graph. The number of the namespace in which the reference type
        is defined can be specified to further narrow the search. If none is provided
        it will return all namespaces"""

        object_type_nodes = self.nodes[self.nodes["NodeClass"] == node_class]

        if namespace is not None:
            object_type_nodes.reset_index(inplace=True)
            mask = (
                object_type_nodes["NodeId"].map(lambda x: x.namespace) == namespace
            )
            object_type_nodes = object_type_nodes[mask]

        return object_type_nodes["BrowseName"].unique().tolist()

    def get_nodes_classes(self):
        return self.nodes["NodeClass"].unique().tolist()

    def get_instances_with_type_info(self):
        """Returns the UAObjects and the browsename of their type"""
        nodes = self.nodes[["NodeClass", "BrowseName", "NodeId", "id"]].set_index('id', drop=False)
        has_type_def_id = self.reference_type_by_browsename("HasTypeDefinition")
        htd = self.references.loc[self.references['ReferenceType'] == has_type_def_id, [['Src', 'Trg']]]
        typeinfo = nodes.rename(columns={'BrowseName':'TypeBrowseName', 'NodeId':'TypeNodeId',
                                         'id':'Typeid'}, errors='raise').drop(columns=['NodeClass'])
        htd = htd.set_index('Src').join(nodes).set_index('Trg').join(typeinfo)
        return htd

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

        if has_property_name == 'EnumStrings':
            ua_list_of = has_property_node["Value"].values[0]
            for localized_text_i, localized_text in enumerate(ua_list_of.value):
                enum_dict[localized_text_i] = localized_text.text
        else:
            raise NotImplementedError('EnumValues not implemented')

        return enum_dict

    def get_enum_string(self, enum_name: str, number: int):
        """This function will return the string value of within an enum,
        provided you get both the of the enum and an integer value."""
        enum_dict = self.get_enum_dict(enum_name)
        #TODO: Cache enumdict for performance
        return enum_dict[number]

    def get_enum_int(self, enum_name: str, string: str):
        """This function will return the integer value of within an enum,
        provided you get both the of the enum and a string value."""
        # Ad Hoc solution to ensure text in files does not include newlines and line breaks
        string = string.replace("\r", "")
        string = string.replace("\n", "")
        enum_dict = self.get_enum_dict(enum_name)
        # TODO: Cache enumdict for performance
        # Getting the dict key based on the value
        key_list = list(enum_dict.keys())
        val_list = list(enum_dict.values())
        try:
            position = val_list.index(string)
            return key_list[position]
        except:
            raise ValueError(
                "Could not find the string: {}, for the enum_name: {}".format(
                    string, enum_name
                )
            )

    def get_objects_of_type(self, type_name: str):
        has_type_def = self.reference_type_by_browsename("HasTypeDefinition")
        object_type_df = self.object_type_by_browsename(type_name)
        reference_ids = self.references[
            (self.references["ReferenceType"] == has_type_def)
            & (self.references["Trg"] == object_type_df)
        ]
        return self.nodes.loc[self.nodes["id"].isin(reference_ids["Src"])]

import pandas as pd
from opcua_tools import UANodeId

from .nodeset_parser import parse_xml_dir
from .navigation import resolve_ids_from_browsenames
from .nodeset_generator import create_nodeset2_file
from typing import List, Optional, Union
from io import StringIO
from datetime import datetime

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


    def write_nodeset(self, filename_or_stringio: Union[str, StringIO], namespace_uri: str,
                      include_outgoing_instance_level_references: Optional[bool] = True,
                      last_modified: Optional[datetime] = None,
                      publication_date: Optional[datetime] = None):
        if namespace_uri not in self.namespaces:
            raise ValueError('Could not find namespace uri: ' + namespace_uri)
        namespace_index = self.namespaces.index(namespace_uri)
        if not include_outgoing_instance_level_references:
            use_references = self.remove_instance_level_outgoing_references(namespace_index=namespace_index)
        else:
            use_references = self.references

        #Always serialize namespace 1 in xml, so we need to remap indices
        new_namespaces_list = [self.namespaces[0], self.namespaces[namespace_index]]
        for i,n in enumerate(self.namespaces):
            if i != 0 and i != namespace_index:
                new_namespaces_list.append(n)

        remapper = {i:new_namespaces_list.index(n) for i,n in enumerate(self.namespaces)}
        use_nodes = self.nodes.copy()
        use_nodes['NodeId'] = use_nodes['NodeId'].map(
            lambda x:UANodeId(namespace=remapper[x.namespace],
                              value=x.value,
                              nodeid_type=x.nodeid_type))

        create_nodeset2_file(nodes=use_nodes,
                             references=use_references,
                             serialize_namespace=1,
                             namespaces=new_namespaces_list,
                             filename_or_stringio=filename_or_stringio,
                             last_modified=last_modified,
                             publication_date=publication_date)


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

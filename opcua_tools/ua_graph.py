import pandas as pd
from .nodeset_parser import parse_xml_dir
from .navigation import resolve_ids_from_browsenames
from .nodeset_generator import create_nodeset2_file
from typing import List

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

        object_nodes = self.nodes[self.nodes['NodeClass'] == 'UAObjectType']
        object_ids = resolve_ids_from_browsenames(nodes=object_nodes, browsenames=[browsename])
        if len(object_ids) == 0:
            raise ValueError('Could not find object ' + browsename)
        elif len(object_ids) > 1:
            raise ValueError('Multiple hits for object ' + browsename + ' please specify namespace')
        else:
            reference_type_id = object_ids.iloc[0]

        return int(reference_type_id)


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

    def write_nodeset(self, filename_or_stringio:str, namespace_uri:str):
        if namespace_uri not in self.namespaces:
            raise ValueError('Could not find namespace uri: ' + namespace_uri)
        namespace_index = self.namespaces.index(namespace_uri)
        lookup_df = self.nodes[['id', 'NodeId']].rename(columns={'NodeId': 'uniques'}).set_index('id', drop=True)
        create_nodeset2_file(nodes=self.nodes, references=self.references,
                             serialize_namespace=namespace_index,
                             lookup_df=lookup_df,
                             namespaces=self.namespaces,
                             filename_or_stringio=filename_or_stringio)



import opcua_tools as ot
from opcua_tools.nodeset_generator import denormalize_nodeids
import os
import pandas as pd
PATH_HERE = os.path.dirname(__file__)


def test_idempotency():
    parse_dict = ot.parse_xml_dir(PATH_HERE + '/testdata/generator')
    ot.create_nodeset2_file(nodes=parse_dict['nodes'].copy(),
                            references=parse_dict['references'].copy(),
                            lookup_df=parse_dict['lookup_df'].copy(),
                            namespaces=parse_dict['namespaces'],
                            serialize_namespace=0,
                            filename=PATH_HERE + '/expected/generator/nodeset2.xml')
    parse_dict2 = ot.parse_xml_dir(PATH_HERE + '/expected/generator')

    nodes = parse_dict['nodes']
    references = parse_dict['references']
    nodes, references = denormalize_nodeids(nodes, references, parse_dict['lookup_df'])
    nodes = nodes.drop(columns=['id'])
    nodes = nodes.sort_values(by=nodes.columns.values.tolist()).reset_index(drop=True)
    references = references.sort_values(by=references.columns.values.tolist()).reset_index(drop=True)

    nodes2 = parse_dict2['nodes']
    references2 = parse_dict2['references']
    nodes2, references2 = denormalize_nodeids(nodes2, references2, parse_dict2['lookup_df'])
    nodes2 = nodes2.drop(columns=['id'])
    nodes2 = nodes2.sort_values(by=nodes.columns.values.tolist()).reset_index(drop=True)
    references2 = references2.sort_values(by=references.columns.values.tolist()).reset_index(drop=True)

    #print(set(nodes['Value'].tolist()).difference(set(nodes2['Value'].tolist())))

    #print(nodes[nodes['DataType'].values != nodes2['DataType'].values][['NodeId', 'DataType']])
    #print(nodes2[nodes2['DataType'].values != nodes['DataType'].values][['NodeId', 'DataType']])

    assert set(nodes.columns.values.tolist()) == set(nodes2.columns.values.tolist())

    nodes2 = nodes2[nodes.columns.values.tolist()].copy()
    #nodes2.to_csv('nodes2.csv')
    #nodes.to_csv('nodes.csv')
    pd.testing.assert_frame_equal(nodes, nodes2)
    pd.testing.assert_frame_equal(references, references2)

    os.remove(PATH_HERE + '/expected/generator/nodeset2.xml')


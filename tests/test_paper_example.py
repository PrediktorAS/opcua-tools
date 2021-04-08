import opcua_tools as ot
from opcua_tools.nodeset_generator import denormalize_nodeids
import os
PATH_HERE = os.path.dirname(__file__)

def test_values_correct():
    parse_dict = ot.parse_xml_dir(PATH_HERE + '/testdata/paper_example')

    nodes = parse_dict['nodes']
    references = parse_dict['references']
    nodes, references = denormalize_nodeids(nodes, references, parse_dict['lookup_df'])
    nodes = nodes.drop(columns=['id'])
    nodes = nodes.sort_values(by=nodes.columns.values.tolist()).reset_index(drop=True)

    nodes = nodes[nodes['ns'] == 1] #Select only example namespace.

    nodes.to_csv(PATH_HERE + '/expected/paper_example/nodes.csv', index=False)

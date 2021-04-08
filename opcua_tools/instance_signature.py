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

import time

from .navigation import supertypes_of_nodes, hierarchical_references_trg_has_modelling_rule, \
    has_modelling_rule_references, find_relatives
import pandas as pd
from typing import List

def fully_inherited_instance_declarations(request_type_ids:List[str], type_nodes:pd.DataFrame, type_references:pd.DataFrame):

    if len(request_type_ids) == 0:
        raise ValueError('Called without any requested types')

    if len(type_nodes) == 0:
        raise ValueError('Called without any type-library nodes')

    require_type_node_cols = {'id','BrowseName'}
    if not all(n in type_nodes.columns.values for n in require_type_node_cols):
        raise ValueError('One of required columns ' + str(require_type_node_cols) + '  missing from type_nodes')

    require_type_references_cols = {'Src','Trg', 'ReferenceType'}
    if not all(n in type_references.columns.values for n in require_type_references_cols):
        raise ValueError('One of required columns ' + str(require_type_references_cols) + '  missing from type_references')

    want_types = set(request_type_ids)
    have_types = set(type_nodes[type_nodes['NodeClass'].str.endswith('Type')]['id'].values)
    missing_types = want_types-have_types
    if len(missing_types) > 0:
        raise ValueError('Missing requested types from type nodes: ' + str(missing_types))

    time_start = time.time()
    supertypes = supertypes_of_nodes(types_to_supertype=request_type_ids,
                                        type_nodes=type_nodes,
                                        type_references=type_references)[::-1].reset_index(drop=True)
    assert set(supertypes.columns.values.tolist()) == {'type', 'supertype'}

    supertypes['index'] = supertypes.groupby('type').cumcount().reset_index(drop=True)
    assert set(supertypes.columns.values.tolist()) == {'index', 'supertype', 'type'}

    hierarchical_refs_has_modelling_rule = hierarchical_references_trg_has_modelling_rule(
        references=type_references,
        type_references=type_references,
        type_nodes=type_nodes)
    assert set(hierarchical_refs_has_modelling_rule.columns.values.tolist()) == {'Src', 'Trg', 'ReferenceType'}

    inst_decl = find_relatives(supertypes, 'supertype', hierarchical_refs_has_modelling_rule, 'desc', keep_paths=True)

    levels = [c for c in inst_decl.columns.values if type(c) == int]
    inh_melt = inst_decl.melt(id_vars=['supertype', 'index', 'type', 'len_path', 'end'], value_vars=levels,
                              var_name='path',
                              value_name='instance').dropna()
    inh_melt = inh_melt.set_index('instance').join(type_nodes.set_index('id')[['BrowseName']])
    inh_melt.loc[inh_melt['len_path'] == 0, 'BrowseName'] = ''
    has_modelling_rule = has_modelling_rule_references(inst_references=type_references,
                                                          type_nodes=type_nodes,
                                                          type_references=type_references)
    inh_melt = inh_melt.join(has_modelling_rule.set_index('Src')[['Trg']]).reset_index().rename(
        columns={'level_0': 'instance'})
    inh_melt = inh_melt.set_index('Trg').join(type_nodes.set_index('id')[['BrowseName']],
                                              rsuffix='_ModellingRule').reset_index(drop=True)
    inh_melt = inh_melt[(~inh_melt['BrowseName_ModellingRule'].isna()) | (inh_melt['len_path'] == 0)]
    inh_melt = inh_melt.sort_values(by=['type', 'index', 'end', 'path'])
    inh_tree = inh_melt.groupby(by=['type', 'index', 'supertype', 'end']).agg({
        'BrowseName': lambda x: '/'.join(x.to_list()),
        'BrowseName_ModellingRule': lambda x: x.dropna().to_list()})
    inh_tree = inh_tree.reset_index().sort_values(by=['type', 'index', 'BrowseName'], ascending=False)
    dup_nodes = inh_tree.duplicated(subset=['BrowseName', 'type'])
    inh_tree = inh_tree[~dup_nodes].reset_index(drop=True)
    subnodes_of_placeholders = inh_tree['BrowseName_ModellingRule'].map(
        lambda x: ('OptionalPlaceholder' in x or 'MandatoryPlaceholder' in x) and len(x) > 1)
    inh_tree = inh_tree[~subnodes_of_placeholders]
    fully_inherited = inh_tree.rename(
        columns={'end': 'InstanceId', 'BrowseName': 'BrowsePath', 'type': 'TypeId',
                 'supertype': 'SuperTypeId', 'BrowseName_ModellingRule': 'ModellingRulePath'}, errors='raise').drop(columns='index')
    print(
        'Creating fully inherited instance declarations took: ' + str(round(time.time() - time_start, 2)) + ' seconds')
    return fully_inherited

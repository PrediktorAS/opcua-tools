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

import os
from typing import Optional
import time
from xml.sax.saxutils import escape
import lxml.etree as ET
from datetime import datetime
import pytz
import pandas as pd
from typing import List

PATH_HERE = os.path.dirname(__file__)

simplevariants = {'Boolean', 'SByte', 'Byte', 'Int16', 'UInt16', 'Int32', 'UInt32', 'Int64', 'UInt64', 'Float',
                  'Double', 'String', 'DateTime', 'Guid', 'ByteString'}


def create_header_xml(namespaces, serialize_namespace, xmlns_dict=None, last_modified:Optional[datetime] = None, publication_date: Optional[datetime] = None):
    if xmlns_dict is None:
        xmlns_dict = {'xsd': 'http://www.w3.org/2001/XMLSchema',
                      'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                      None: 'http://opcfoundation.org/UA/2011/03/UANodeSet.xsd'}

    if last_modified is None:
        last_modified = datetime.now(tz=pytz.UTC)

    if publication_date is None:
        publication_date = datetime.now(tz=pytz.UTC)

    header = '<?xml version="1.0" encoding="utf-8"?>\n'
    header += '<UANodeSet'
    header += ' LastModified="' + last_modified.isoformat() + '"'
    for k in xmlns_dict:
        if k is None:
            prefix = 'xmlns'
        else:
            prefix = 'xmlns:' + k
        header += ' ' + prefix + '="' + xmlns_dict[k] + '"'
    header += '>\n'
    if len(namespaces) > 1:
        header += '<NamespaceUris>\n'
        for i, n in enumerate(namespaces):
            if i != serialize_namespace:
                header += '<Uri>' + n + '</Uri>\n'
        header += '</NamespaceUris>\n'
    header += '<Models><Model ModelUri="' +  namespaces[serialize_namespace] + '" PublicationDate="' +\
              publication_date.isoformat() + '" Version="1.0.0"></Model></Models>\n'
    header += '<Aliases></Aliases>\n'
    return header

def generate_references_xml(nodes, references):
    '''
    :param nodes:
    :param references:
    :return:
    '''

    # references = references.reset_index()
    nodes['target_same_ns'] = True
    references = references.set_index('Trg').join(nodes.set_index('NodeId')[['target_same_ns']], how='left')
    references = references.reset_index().rename(columns={'index': 'Trg'})
    nodes.drop(columns='target_same_ns', inplace=True)
    references['target_same_ns'] = ~references['target_same_ns'].isna()

    # Default code references on target node
    references['NodeId'] = references['Trg']

    # References where target is not in same namespace are encoded on source
    references.loc[~references['target_same_ns'], 'NodeId'] = references.loc[~references['target_same_ns'], 'Src']

    # Outgoing reference when target is not in same nodeset
    references.loc[~references['target_same_ns'], 'xml'] = '<Reference ReferenceType="' + references.loc[
        ~references['target_same_ns'], 'ReferenceType'] + \
                                                           '">' + references.loc[
                                                               ~references['target_same_ns'], 'Trg'] + '</Reference>'

    # Incoming reference only when target is in same nodeset to be generated
    references.loc[references['target_same_ns'], 'xml'] = '<Reference ReferenceType="' + references.loc[
        references['target_same_ns'], 'ReferenceType'] + \
                                                          '"  IsForward="false">' + references.loc[
                                                              references['target_same_ns'], 'Src'] + '</Reference>'

    references = references.drop(columns=['target_same_ns'])
    return references


def encode_values(nodes):
    is_variable = nodes['NodeClass'] == 'UAVariable'
    if 'Value' in nodes.columns.values:
        has_value = ~nodes['Value'].isna()
    else:
        has_value = False

    should_encode = is_variable & has_value

    nodes.loc[should_encode, 'EncodedValue'] = nodes.loc[should_encode, 'Value'].map(lambda x:x.xml_encode(include_xmlns=True))


def generate_nodes_xml(nodes:pd.DataFrame, references:pd.DataFrame, lookup_df:pd.DataFrame):
    assert nodes['BrowseNameNamespace'].isna().sum() == 0, 'Should not have missing BrowseNameNamespaces'

    replacer = lambda x: x.map(escape)
    nodes['DisplayName'] = replacer(nodes['DisplayName'])
    nodes['BrowseName'] = replacer(nodes['BrowseName'])
    nodes['NodeId'] = replacer(nodes['NodeId'].map(str))

    nodes, references = denormalize_nodeids(nodes, references, lookup_df=lookup_df)

    references['Src'] = replacer(references['Src'].map(str))
    references['Trg'] = replacer(references['Trg'].map(str))
    references['ReferenceType'] = replacer(references['ReferenceType'].map(str))


    nodes = nodes.copy()

    encode_values(nodes)
    nodes['nodexml'] = '<' + nodes['NodeClass'] + ' NodeId="' + nodes['NodeId'] + '"'
    if ['SymbolicName'] in nodes.columns.values:
        hasSymbolicName = ~nodes['SymbolicName'].isna()
        nodes.loc[hasSymbolicName, 'nodexml'] = nodes.loc[hasSymbolicName, 'nodexml'] + ' SymbolicName="' + nodes.loc[
            hasSymbolicName, 'SymbolicName'] + '" '
    nodes['nodexml'] = nodes['nodexml'] + ' BrowseName="' + nodes['BrowseNameNamespace'].astype(str) + ':' + nodes['BrowseName'] + '" '
    for a in ['DataType', 'ValueRank', 'AccessLevel', 'UserAccessLevel', 'IsAbstract', 'Symmetric', 'ParentNodeId', 'ArrayDimensions', 'MinimumSamplingInterval', 'MethodDeclarationId', 'EventNotifier']:
        if a in nodes.columns.values:
            notna = ~nodes[a].isna()
            haslen = nodes[a].astype(str).str.len() > 0
            nodes.loc[notna & haslen, 'nodexml'] = nodes.loc[notna & haslen, 'nodexml'] + a + '="' + nodes.loc[
                notna & haslen, a].astype(str) + '" '

    nodes['nodexml'] = nodes['nodexml'] + '>'
    nodes['nodexml'] = nodes['nodexml'] + '<DisplayName>' + nodes['DisplayName'] + '</DisplayName>'
    has_description = ~nodes['Description'].isna()
    nodes.loc[has_description, 'nodexml'] = nodes.loc[has_description, 'nodexml'] + '<Description>' + nodes.loc[has_description, 'Description'] + '</Description>'

    new_references = generate_references_xml(nodes, references).reset_index()
    nodes_tojoin = nodes.set_index('NodeId').join(new_references.set_index('NodeId')[['xml']])

    nodes_tojoin['xml'] = nodes_tojoin['xml'].fillna('')
    nodes_tojoin = nodes_tojoin.reset_index().groupby('NodeId').agg({'xml': lambda x: ''.join(x.values)})[['xml']]
    nodes = nodes.set_index('NodeId').join(nodes_tojoin).reset_index()
    nodes['nodexml'] = nodes['nodexml'] + '<References>' + nodes['xml'].fillna('') + '</References>'
    has_encoded_value = ~nodes['EncodedValue'].isna()
    nodes.loc[has_encoded_value, 'nodexml'] = nodes.loc[has_encoded_value, 'nodexml'] + '<Value>' + \
                                              nodes.loc[has_encoded_value, 'EncodedValue'] + '</Value>'

    nodes['nodexml'] = nodes['nodexml'] + '</' + nodes['NodeClass'] + '>'
    return nodes['nodexml'].astype(str)


def create_nodeset2_file(nodes:pd.DataFrame, references:pd.DataFrame, lookup_df:pd.DataFrame,
                         namespaces:List[str], serialize_namespace:int, filename='nodeset2.xml',
                         xmlns_dict=None, last_modified:Optional[datetime] = None, publication_date: Optional[datetime] = None):
    header = create_header_xml(namespaces, serialize_namespace, xmlns_dict=xmlns_dict, last_modified=last_modified,
                               publication_date=publication_date)
    start_time = time.time()
    print('Creating nodeset2xml-node-string')
    nodes_df = generate_nodes_xml(nodes, references, lookup_df)
    end_time = time.time()
    print('Creating nodeset2xml-string took ' + str(end_time - start_time))
    print('Writing nodeset2xml')
    start_time = time.time()
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(nodes_df.values))
        f.write('\n')
        f.write('</UANodeSet>')
    end_time = time.time()
    print('Writing nodeset2xml-file took: ' + str(end_time - start_time))


def validate_nodeset2_file(filename:str):
    start_time = time.time()
    tree = ET.parse(PATH_HERE + '/static/UANodeSet.xsd')
    schema = ET.XMLSchema(tree)
    parser = ET.XMLParser(schema=schema)
    try:
        ET.parse(filename, parser)
        print('XML validated by nodeset2 xsd')
    except Exception as e:
        print('XML is invalid according to nodeset2 xsd')
        print('Error occured:')
        print(e)
    end_time = time.time()
    print('Validating nodeset2xml-file took: ' + str(end_time - start_time))


def denormalize_nodeids(nodes, references, lookup_df):
    nodecols = ['ParentNodeId', 'DataType', 'MethodDeclarationId']
    refcols = ['Src', 'Trg', 'ReferenceType']

    for c in refcols:
        uniques = lookup_df.rename(columns={'uniques':c}, errors='raise')
        references = references.set_index(c).join(uniques).reset_index(drop=True)

    for c in nodecols:
        if c in nodes.columns.values:
            uniques = lookup_df.rename(columns={'uniques': c}, errors='raise')
            nodes = nodes.set_index(c).join(uniques).reset_index(drop=True)

    return nodes, references
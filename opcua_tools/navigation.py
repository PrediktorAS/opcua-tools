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

from typing import List, Union
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, eye
from opcua_tools.value_parser import parse_nodeid


def supertypes_of_nodes(
    types_to_supertype: List[str],
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
) -> pd.DataFrame:
    # Computes the closure
    closure = typing_transitive_reflexive(type_nodes, type_references)
    closure = closure.set_index("Trg")
    typeindex = pd.Index(types_to_supertype)
    closure = closure[closure.index.isin(typeindex)].reset_index()
    closure = closure.rename(columns={"Src": "supertype", "Trg": "type"})

    return closure


def hierarchical_references_trg_has_modelling_rule(
    references: pd.DataFrame, type_references: pd.DataFrame, type_nodes: pd.DataFrame
):
    hierarchical_refs = hierarchical_references(
        inst_references=references,
        type_references=type_references,
        type_nodes=type_nodes,
    )
    has_modelling_rule = has_modelling_rule_references(
        inst_references=references,
        type_references=type_references,
        type_nodes=type_nodes,
    )[["Src"]].rename(columns={"Src": "id"})
    hierarchical_refs_has_modelling_rule = hierarchical_refs.set_index("Trg").join(
        has_modelling_rule.set_index("id"), how="inner"
    )
    hierarchical_refs_has_modelling_rule = (
        hierarchical_refs_has_modelling_rule.reset_index().rename(
            columns={"index": "Trg"}
        )
    )
    return hierarchical_refs_has_modelling_rule[["Src", "Trg", "ReferenceType"]].copy()


# Useful for keeping forward refs for methods when instantiating
def hierarchical_references_trg_has_no_modelling_rule(
    references: pd.DataFrame, type_references: pd.DataFrame, type_nodes: pd.DataFrame
):
    hierarchical_refs = hierarchical_references(
        inst_references=references,
        type_references=type_references,
        type_nodes=type_nodes,
    )
    has_modelling_rule = has_modelling_rule_references(
        inst_references=references,
        type_references=type_references,
        type_nodes=type_nodes,
    )[["Src"]].rename(columns={"Src": "id"})
    has_modelling_rule = has_modelling_rule.set_index("id")
    hierarchical_refs_has_no_modelling_rule = hierarchical_refs.set_index(
        "Trg", drop=False
    )
    trg_no_modelling_rule = ~hierarchical_refs_has_no_modelling_rule.index.isin(
        has_modelling_rule.index
    )
    hierarchical_refs_has_no_modelling_rule = hierarchical_refs_has_no_modelling_rule[
        trg_no_modelling_rule
    ].copy()
    return hierarchical_refs_has_no_modelling_rule[
        ["Src", "Trg", "ReferenceType"]
    ].copy()


def non_hierarchical_references_trg_has_no_modelling_rule(
    references: pd.DataFrame, type_references: pd.DataFrame, type_nodes: pd.DataFrame
) -> pd.DataFrame:
    """This function expects a table of references on which to find the subset
    of references containing only references of the subtype "NonHierarchicalReferences" in
    OPC UA standard, which point to nodes which do no not have a reference to a ModellingRule Node.
    In order to do this the function also requires tables of the nodes and references which describe
    the types in the references table.

    Instance Declarations require having a HasModellingRule reference to a Modelling Rule.
    If this function is used in a type namespace, it will produce non-hierarchical reference
    types which do not point to InstanceDeclarations.

    Args:
        references (pd.DataFrame): A table of references on which to perform the sub-setting on.
        type_references (pd.DataFrame): A table of references describing the type namespace.
        type_nodes (pd.DataFrame): A table of nodes describing the type namespace.

    Returns:
        pd.DataFrame: Dataframe containing the list of all non-hierarchical references where the
            target is a node which does not have a reference to a Modelling Rule node.

    """

    non_hierarchical_refs = non_hierarchical_references(
        inst_references=references,
        type_references=type_references,
        type_nodes=type_nodes,
    )
    has_modelling_rule = has_modelling_rule_references(
        inst_references=references,
        type_references=type_references,
        type_nodes=type_nodes,
    )[["Src"]].rename(columns={"Src": "id"})
    has_modelling_rule = has_modelling_rule.set_index("id")
    non_hierarchical_refs_has_no_modelling_rule = non_hierarchical_refs.set_index(
        "Trg", drop=False
    )
    trg_no_modelling_rule = ~non_hierarchical_refs_has_no_modelling_rule.index.isin(
        has_modelling_rule.index
    )
    non_hierarchical_refs_has_no_modelling_rule = non_hierarchical_refs_has_no_modelling_rule[
        trg_no_modelling_rule
    ].copy()
    return non_hierarchical_refs_has_no_modelling_rule[
        ["Src", "Trg", "ReferenceType"]
    ].copy()

def find_relatives(
    nodes: pd.DataFrame,
    nodes_key_col: str,
    edges: pd.DataFrame,
    relative_type: str,
    cutoff: int = None,
    keep_paths: bool = False,
) -> pd.DataFrame:
    """
    Find the relatives to the provided nodes

    The

    Parameters:
    nodes (pd.DataFrame): The dataframe with nodes to find relatives from.
    nodes_key_col (str): The key column to use for indexing in the nodes DataFrame
    edges(pd.DataFrame): The edges to follow in the traverse
    cutoff (int): Max number of steps to go for the traverse
    keep_paths(bool):

    Returns:


    """
    new_nodes = nodes.copy()
    orig_cols = nodes.columns.values.tolist()
    new_nodes[0] = nodes[nodes_key_col]
    new_nodes["len_path"] = 0
    new_nodes = new_nodes.set_index(0, drop=False)
    path_cols = [0]
    if relative_type.lower().startswith("a"):
        col_src = "Trg"
        col_trg = "Src"
    else:
        col_src = "Src"
        col_trg = "Trg"
    # Set the index on reference column based on relativetype(direction)
    edge_join = edges.set_index(col_src)
    result = [new_nodes]
    i = 1
    while (new_nodes.shape[0] > 0) and ((cutoff is None) or (cutoff >= i)):
        joined_nodes = new_nodes.join(edge_join, how="inner")
        #
        new_nodes = joined_nodes[orig_cols + [col_trg] + path_cols].copy()
        if len(new_nodes) > 0:
            if keep_paths:
                new_nodes[i] = new_nodes[col_trg]
                path_cols.append(i)
            else:
                new_nodes[0] = new_nodes[col_trg]
            new_nodes["len_path"] = i
            new_nodes = new_nodes.set_index(col_trg)
            result.append(new_nodes)
        i = i + 1
    if len(result) > 1:
        resconc = pd.concat(result).reset_index()
    else:
        resconc = result[0]

    resconc["end"] = resconc[0]
    if keep_paths:
        for i in range(1, i - 1):
            resconc["end"] = resconc[i].combine_first(resconc["end"])

    return resconc


def resolve_id_from_nodeid(nodes: pd.DataFrame, nodeid: str):
    nodeid_instance = parse_nodeid(nodeid)
    nodes = nodes.set_index("NodeId")
    theid = nodes.loc[nodeid_instance, "id"]
    return theid


def resolve_ids_from_browsenames(nodes: pd.DataFrame, browsenames: List[str]):
    nodes = nodes.set_index("BrowseName")
    hst_id = nodes.loc[browsenames, "id"].reset_index(drop=True)
    return hst_id


def has_subtype_references(
    references: pd.DataFrame, type_nodes: pd.DataFrame, id_col: str
) -> pd.DataFrame:
    hst_id = type_nodes.loc[
        (type_nodes["NodeClass"] == "UAReferenceType")
        & (type_nodes["BrowseName"] == "HasSubtype"),
        id_col,
    ].iloc[0]
    subtype = references[references["ReferenceType"] == hst_id].copy()
    return subtype


def has_type_definition_references(
    references: pd.DataFrame, type_nodes: pd.DataFrame
) -> pd.DataFrame:
    htd_id = type_nodes.loc[
        (type_nodes["NodeClass"] == "UAReferenceType")
        & (type_nodes["BrowseName"] == "HasTypeDefinition"),
        "id",
    ].iloc[0]
    htd = references[references["ReferenceType"] == htd_id].copy()
    return htd


def has_property_references(
    inst_references: pd.DataFrame,
    type_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
) -> pd.DataFrame:
    propref_id = type_nodes.loc[
        (type_nodes["NodeClass"] == "UAReferenceType")
        & (type_nodes["BrowseName"] == "HasProperty"),
        "id",
    ].iloc[0]
    prop_ref = constrain_to_reference_type(
        inst_references, type_nodes, type_references, [propref_id]
    )
    return prop_ref


def has_modelling_rule_references(
    inst_references: pd.DataFrame,
    type_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
) -> pd.DataFrame:
    propref_id = type_nodes.loc[
        (type_nodes["NodeClass"] == "UAReferenceType")
        & (type_nodes["BrowseName"] == "HasModellingRule"),
        "id",
    ].iloc[0]
    prop_ref = constrain_to_reference_type(
        inst_references, type_nodes, type_references, [propref_id]
    )
    return prop_ref


def hierarchical_references(
    inst_references: pd.DataFrame,
    type_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
) -> pd.DataFrame:
    hierref_id = type_nodes.loc[
        (type_nodes["NodeClass"] == "UAReferenceType")
        & (type_nodes["BrowseName"] == "HierarchicalReferences"),
        "id",
    ].iloc[0]
    prop_ref = constrain_to_reference_type(
        inst_references, type_nodes, type_references, [hierref_id]
    )
    return prop_ref


def non_hierarchical_references(
    inst_references: pd.DataFrame,
    type_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
) -> pd.DataFrame:
    """This function expects a table of references on which to find the subset
    of references containing only references of the subtype "NonHierarchicalReferences"
    in OPC UA standard. In order to do this the function also requires tables of the
    nodes and references which describe the types in the references table.

    Args:
        inst_references (pd.DataFrame): A table of references on which to perform the sub-setting on.
        type_references (pd.DataFrame): A table of references describing the type namespace.
        type_nodes (pd.DataFrame): A table of nodes describing the type namespace.

    Returns:
        pd.DataFrame: Dataframe containing the list of all non-hierarchical references.

    """

    non_hierref_id = type_nodes.loc[
        (type_nodes["NodeClass"] == "UAReferenceType")
        & (type_nodes["BrowseName"] == "NonHierarchicalReferences"),
        "id",
    ].iloc[0]
    prop_ref = constrain_to_reference_type(
        inst_references, type_nodes, type_references, [non_hierref_id]
    )
    return prop_ref


def fast_transitive_closure(references: pd.DataFrame) -> pd.DataFrame:
    # Quickly and memory-efficiently compute the transitive closure of a reference
    # Transitive closure: https://en.wikipedia.org/wiki/Transitive_closure
    # We do not consider ReferenceType or store underlying paths in this closure
    # The references are converted to a matrix where each unique Src/Trg is assigned a column and row
    # We have row(Src), col(Trg) == 1 if there is a reference from Src to Trg, 0 otherwise
    # A sparse matrix representation is used in order to reduce memory consumption.
    # The transitive closure is given by iterative dot products of this matrix with itself until we reach a fixed point
    # At the end of each iteration, a cell is converted to 1 if it is above 0 or 0 otherwise.
    # This is in order to ensure that the algorithm terminates
    assert (
        references["Src"] == references["Trg"]
    ).sum() == 0, "There should be no references r such that r(n,n)"
    codes, uniques = pd.factorize(pd.concat([references["Src"], references["Trg"]]))
    src_codes = codes[0 : references.shape[0]]
    trg_codes = codes[references.shape[0] :]
    data = np.ones(references.shape[0])
    sparmat = coo_matrix(
        (data, (src_codes, trg_codes)),
        shape=(uniques.shape[0], uniques.shape[0]),
        dtype=bool,
    )
    sparmat = sparmat + eye(uniques.shape[0])
    fixedp = False
    while not fixedp:
        before = sparmat
        sparmat = sparmat.dot(sparmat) > 0
        if before.sum(axis=None) == sparmat.sum(axis=None):
            fixedp = True

    sparmat = sparmat - eye(uniques.shape[0])
    sparmat = sparmat.tocoo()
    src = sparmat.row
    trg = sparmat.col
    src_nids = uniques.take(src)
    trg_nids = uniques.take(trg)
    hierarchy = pd.DataFrame({"Src": src_nids, "Trg": trg_nids})
    return hierarchy


def fast_hierarchy_transitive_closure(
    inst_references: pd.DataFrame,
    constrained_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
    interesting_types: pd.Series,
) -> pd.DataFrame:
    # Computes a navigation hierarchy between instances of interesting_types
    # The navigation hierarchy is first computed between all types (given references in inst_references)
    # Then, it is restricted to only concern instances of interesting_types
    constrained_references = constrained_references[["Src", "Trg", "ReferenceType"]]
    hierarchy = fast_transitive_closure(constrained_references)

    types = type_nodes[type_nodes["NodeClass"].str.endswith("Type")].set_index(
        "BrowseName"
    )
    interesting_ids_types = types.loc[pd.Index(interesting_types), "id"].to_list()

    sub_inter_types = subtypes_of_nodes(
        interesting_ids_types, type_nodes, type_references
    )
    inter_subtypes_index = pd.Index(sub_inter_types["subtype"])
    htd = has_type_definition_references(inst_references, type_nodes).set_index("Trg")
    htd = htd[htd.index.isin(inter_subtypes_index)]
    inst_inter_type_index = pd.Index(htd["Src"])

    hierarchy = hierarchy.set_index("Src")
    hierarchy = hierarchy[hierarchy.index.isin(inst_inter_type_index)].reset_index()
    hierarchy = hierarchy.set_index("Trg")
    hierarchy = hierarchy[hierarchy.index.isin(inst_inter_type_index)].reset_index()
    return hierarchy


def signal_variables(
    instance_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
) -> pd.DataFrame:
    reftypes = type_nodes[type_nodes["NodeClass"] == "UAVariableType"]
    signalvar_type = reftypes.loc[
        reftypes["BrowseName"] == "BaseDataVariableType", "id"
    ].iloc[0]
    signalvar_types = subtypes_of_nodes([signalvar_type], type_nodes, type_references)
    signalvar_types_index = pd.Index(signalvar_types["subtype"])
    inst_htd = has_type_definition_references(instance_references, type_nodes)
    inst_htd = inst_htd.set_index("Trg")
    signal_vars = inst_htd[inst_htd.index.isin(signalvar_types_index)]["Src"]

    return signal_vars


def property_variables(
    instance_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
) -> pd.DataFrame:
    reftypes = type_nodes[type_nodes["NodeClass"] == "UAVariableType"]
    propvar_type = reftypes.loc[reftypes["BrowseName"] == "PropertyType", "id"].iloc[0]
    propvar_types = subtypes_of_nodes([propvar_type], type_nodes, type_references)
    propvar_types_index = pd.Index(propvar_types["subtype"])
    inst_htd = has_type_definition_references(instance_references, type_nodes)
    inst_htd = inst_htd.set_index("Trg")
    prop_vars = inst_htd[inst_htd.index.isin(propvar_types_index)]["Src"]

    return prop_vars


def typing_transitive_reflexive(
    type_nodes: pd.DataFrame, type_references: pd.DataFrame
) -> pd.DataFrame:
    subtype = has_subtype_references(type_references, type_nodes, "id")[["Src", "Trg"]]
    # Add transitive closure
    subtype_closure = fast_transitive_closure(subtype)
    unique_types = pd.concat([type_references["Src"], type_references["Trg"]]).unique()
    # Add reflexive closure
    subtype_closure = pd.concat(
        [subtype_closure, pd.DataFrame({"Src": unique_types, "Trg": unique_types})]
    )
    return subtype_closure


def subtypes_of_nodes(
    types_to_subtype: Union[pd.Series, List[str]],
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
) -> pd.DataFrame:
    # Computes the closure
    closure = typing_transitive_reflexive(type_nodes, type_references)
    closure = closure.set_index("Src")
    typeindex = pd.Index(types_to_subtype)
    closure = closure[closure.index.isin(typeindex)].reset_index()
    closure = closure.rename(columns={"Trg": "subtype", "Src": "type"})

    return closure


def closest_parent(
    inst_nodes: pd.DataFrame,
    inst_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
    interesting_types: List[str],
    uavar_type: str,
) -> pd.DataFrame:
    sub_inter_types = subtypes_of_nodes(interesting_types, type_nodes, type_references)
    inter_subtypes_index = pd.Index(sub_inter_types["subtype"])
    htd = has_type_definition_references(inst_references, type_nodes).set_index("Trg")
    htd = htd[htd.index.isin(inter_subtypes_index)]
    inst_inter_type_index = pd.Index(htd["Src"])

    # Remove incoming edges to objects of desired type
    inst_references = inst_references.set_index("Trg")
    inst_references = inst_references[
        ~inst_references.index.isin(inst_inter_type_index)
    ].reset_index()

    signals = signal_variables(inst_references, type_nodes, type_references)
    signals_index = pd.Index(signals)

    if uavar_type == "Property":
        inst_references = inst_references.set_index("Trg")
        inst_references = inst_references[
            ~inst_references.index.isin(signals_index)
        ].reset_index()

    inst_references_trans = fast_transitive_closure(inst_references[["Src", "Trg"]])
    inst_nodes_ns_index = inst_nodes[["id", "ns"]].set_index("id")
    inst_references_trans = (
        inst_references_trans.set_index("Src")
        .join(inst_nodes_ns_index)
        .reset_index()
        .rename(columns={"index": "Src", "ns": "Src_ns"})
    )
    inst_references_trans = (
        inst_references_trans.set_index("Trg")
        .join(inst_nodes_ns_index)
        .reset_index()
        .rename(columns={"index": "Trg", "ns": "Trg_ns"})
    )

    if uavar_type == "Property":
        properties = property_variables(inst_references, type_nodes, type_references)
        inst_references_trans = inst_references_trans.set_index("Trg")
        inst_references_trans = inst_references_trans[
            inst_references_trans.index.isin(pd.Index(properties))
        ]
        inst_references_trans = inst_references_trans.reset_index().set_index("Src")
        inst_references_trans = inst_references_trans[
            (
                inst_references_trans.index.isin(signals_index)
                | inst_references_trans.index.isin(inst_inter_type_index)
            )
        ]
        inst_references_trans["is_signal"] = inst_references_trans.index.isin(
            signals_index
        )
        inst_references_trans = inst_references_trans.reset_index()
        inst_references_trans = inst_references_trans.sort_values(
            by=["Trg", "is_signal"], ascending=[True, False]
        )
        inst_references_trans = inst_references_trans.drop_duplicates(keep="first")
        inst_references_trans = inst_references_trans.drop(columns="is_signal")
        return inst_references_trans.rename(
            columns={
                "Src": "instance",
                "Trg": "property",
                "Src_ns": "instance_ns",
                "Trg_ns": "property_ns",
            }
        )

    if uavar_type == "Signal":
        inst_references_trans = inst_references_trans.set_index("Trg")
        inst_references_trans = inst_references_trans[
            inst_references_trans.index.isin(signals_index)
        ]
        inst_references_trans = inst_references_trans.reset_index().set_index("Src")
        inst_references_trans = inst_references_trans[
            inst_references_trans.index.isin(inst_inter_type_index)
        ].reset_index()
        inst_references_trans = inst_references_trans.drop_duplicates(keep="first")
        return inst_references_trans.rename(
            columns={
                "Src": "instance",
                "Trg": "variable",
                "Src_ns": "instance_ns",
                "Trg_ns": "variable_ns",
            }
        )


def constrain_to_reference_type(
    inst_references: pd.DataFrame,
    type_nodes: pd.DataFrame,
    type_references: pd.DataFrame,
    reference_types: List[str],
) -> pd.DataFrame:
    subtypes_of_reference = subtypes_of_nodes(
        reference_types, type_nodes, type_references
    )
    inst_references = inst_references.set_index("ReferenceType")
    inst_references = inst_references[
        inst_references.index.isin(pd.Index(subtypes_of_reference["subtype"]))
    ]
    inst_references = inst_references.reset_index()
    return inst_references

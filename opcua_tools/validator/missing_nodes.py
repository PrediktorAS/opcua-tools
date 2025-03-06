import pandas as pd


def raise_missing_nodes_error(
    diff: set[int],
    nodes_df: pd.DataFrame,
    references_df: pd.DataFrame,
    present_column_name: str,
    missing_column_name: str,
):
    if present_column_name == "Trg":
        missing_name = "source"
        present_name = "target"
    else:  # present_column_name == "Src"
        missing_name = "target"
        present_name = "source"

    target_ids_with_no_source = references_df[
        references_df[missing_column_name].isin(diff)
    ]
    nodes_with_no_source = target_ids_with_no_source.join(
        nodes_df, on=present_column_name
    )[["DisplayName", "NodeId", "ReferenceType"]]
    nodes_with_no_source = nodes_with_no_source.set_index("ReferenceType")
    nodes_with_no_source_and_reference_name = nodes_with_no_source.join(
        nodes_df, on=["ReferenceType"], how="left", rsuffix=" (reference)"
    )
    nodes_with_no_source_and_reference_name = (
        nodes_with_no_source_and_reference_name[
            [
                "DisplayName",
                "NodeId",
                "DisplayName (reference)",
                "NodeId (reference)",
            ]
        ]
        .rename(
            columns={
                "DisplayName": f"DisplayName ({present_name})",
                "NodeId": f"NodeId ({present_name})",
            }
        )
        .reset_index()
        .drop(columns=["ReferenceType"])
    )
    raise ValueError(
        f"Some {missing_name} ids do not exist.\n"
        f"These are the {present_name} nodes with missing {missing_name} nodes:\n"
        f"{nodes_with_no_source_and_reference_name.to_string()}"
    )


def raise_missing_source_nodes_error(
    diff: set[int], nodes_df: pd.DataFrame, references_df: pd.DataFrame
):
    raise_missing_nodes_error(diff, nodes_df, references_df, "Trg", "Src")


def raise_missing_target_nodes_error(
    diff: set[int], nodes_df: pd.DataFrame, references_df: pd.DataFrame
):
    raise_missing_nodes_error(diff, nodes_df, references_df, "Src", "Trg")

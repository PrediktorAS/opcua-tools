import pandas as pd

from opcua_tools import constants, ua_data_types
from opcua_tools.validator import exceptions

UALISTOF_CLASS_NAME = ua_data_types.UAListOf.__name__
VALUE_VALIDATION_ERROR_MESSAGE = (
    "Invalid Value for rows with the following display names: {}."
)


def validate_values_in_df(
    df_to_validate: pd.DataFrame, data_type_nodes: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate that the value is valid for the corresponding DataType for all rows in a DataFrame.
    """
    if df_to_validate.empty or "Value" not in df_to_validate.columns:
        return df_to_validate

    not_empty_values_mask = ~df_to_validate["Value"].isna()
    if "NodeClass" in df_to_validate.columns:
        df_with_rows_to_validate = df_to_validate[
            (df_to_validate["NodeClass"] == "UAVariable") & not_empty_values_mask
        ]
    else:
        df_with_rows_to_validate = df_to_validate[not_empty_values_mask]

    if df_with_rows_to_validate.empty:
        return df_to_validate

    if df_with_rows_to_validate["DataType"].isna().any():
        raise exceptions.ValidationError(
            "UAVariables has no DataType! "
            f"Values: {df_to_validate.loc[df_to_validate['DataType'].isna(), 'Value'].to_list()}"
        )

    df_with_rows_to_validate["StringifiedValue"] = df_with_rows_to_validate[
        "Value"
    ].astype(str)
    df_with_rows_to_validate["StringifiedOpcuaToolsClass"] = df_with_rows_to_validate[
        "StringifiedValue"
    ].str.split("(", n=1, expand=True)[0]
    data_types_mapping = constants.DATA_TYPES_MAPPING
    df_with_rows_to_validate["StringifiedDatatypeClass"] = df_with_rows_to_validate[
        "StringifiedOpcuaToolsClass"
    ].replace(data_types_mapping)
    data_int_type_to_data_type_class_mapping = {
        str(k): v for k, v in data_type_nodes["DisplayName"].to_dict().items()
    }

    df_with_rows_to_validate["ExpectedDataType"] = (
        df_with_rows_to_validate["DataType"]
        .astype("str")
        .replace(data_int_type_to_data_type_class_mapping)
    )

    df_with_rows_to_validate["IsValidValue"] = (
        df_with_rows_to_validate["StringifiedDatatypeClass"]
        == df_with_rows_to_validate["ExpectedDataType"]
    )

    simple_data_types_names = list(data_types_mapping.values())
    skip_validation_mask = (
        df_with_rows_to_validate["StringifiedDatatypeClass"] == UALISTOF_CLASS_NAME
    ) | ~df_with_rows_to_validate["ExpectedDataType"].isin(simple_data_types_names)

    potentially_invalid_df = df_with_rows_to_validate[~skip_validation_mask]

    if not potentially_invalid_df["IsValidValue"].all():
        does_not_contain_ua_enumaration_only_mask = ~(
            potentially_invalid_df["StringifiedDatatypeClass"] == "UAEnumeration"
        )
        if not potentially_invalid_df[does_not_contain_ua_enumaration_only_mask].empty:
            invalid_display_names = df_with_rows_to_validate.loc[
                ~df_with_rows_to_validate["IsValidValue"], "DisplayName"
            ]
            invalid_display_names_as_list = invalid_display_names.values.tolist()
            raise exceptions.ValidationError(
                VALUE_VALIDATION_ERROR_MESSAGE.format(invalid_display_names_as_list)
            )
    return df_to_validate

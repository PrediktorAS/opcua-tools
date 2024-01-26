import pandas as pd

from opcua_tools import constants
from opcua_tools.validator import exceptions

VALUE_VALIDATION_ERROR_MESSAGE = (
    "Invalid Value for rows with the following display names: {}."
)


def validate_value(row: pd.Series, original_nodes: pd.DataFrame) -> pd.Series:
    """
    Apply the function to a DataFrame to validate that the value is correct, based on the DataType value.
    """
    variable_node_class_name = "UAVariable"
    if row.get("NodeClass", variable_node_class_name) != variable_node_class_name:
        row["IsValidValue"] = True
        return row

    value_from_row = row.get("Value", pd.NA)
    if pd.isna(value_from_row):
        row["IsValidValue"] = True
        return row

    data_type_from_row = row["DataType"]
    if pd.isna(data_type_from_row):
        raise exceptions.ValidationError(
            f"UAVariable has no DataType! Value: {value_from_row}"
        )

    data_types_mapping = constants.DATA_TYPES_MAPPING
    data_type_display_name = original_nodes[original_nodes["id"] == data_type_from_row][
        "DisplayName"
    ].to_list()[0]

    if (
        value_from_row.__class__ not in data_types_mapping.values()
        or data_type_display_name not in data_types_mapping
    ):
        # The validator can be used to check against the basic data types only.
        row["IsValidValue"] = True
        return row

    expected_opcua_tools_class = constants.DATA_TYPES_MAPPING[data_type_display_name]
    row["IsValidValue"] = isinstance(value_from_row, expected_opcua_tools_class)
    return row


def validate_values_in_df(
    df_to_validate: pd.DataFrame, original_nodes: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate that the value is valid for the corresponding DataType for all rows in a DataFrame.
    """
    if df_to_validate.empty:
        return df_to_validate

    df_to_validate = df_to_validate.apply(
        validate_value, args=(original_nodes,), axis=1
    )

    if not df_to_validate["IsValidValue"].all():
        invalid_display_names = df_to_validate[df_to_validate["IsValidValue"] == False][
            "DisplayName"
        ]
        invalid_display_names_as_list = invalid_display_names.values.tolist()
        raise exceptions.ValidationError(
            VALUE_VALIDATION_ERROR_MESSAGE.format(invalid_display_names_as_list)
        )

    else:
        df_to_validate = df_to_validate.drop(columns=["IsValidValue"])
        return df_to_validate

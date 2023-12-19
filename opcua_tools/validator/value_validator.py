import pathlib

import pandas as pd

from opcua_tools import ua_data_types
from opcua_tools.validator import exceptions

MAPPING_FILE_PATH = (
    pathlib.Path(__file__).parent.parent / "static/data_type_to_value_mapping.csv"
)
OPCUA_TOOLS_CLASSES_TO_SKIP = ["UAEnumeration"]
VALUE_VALIDATION_ERROR_MESSAGE = (
    "Invalid Value for rows with the following display names: {}."
)


def get_data_type_to_value_mapping() -> pd.DataFrame:
    mapping_file_path = MAPPING_FILE_PATH
    return pd.read_csv(mapping_file_path, index_col="DataType")


VALUE_MAPPING = get_data_type_to_value_mapping()


def validate_value(row: pd.Series) -> pd.Series:
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

    if isinstance(data_type_from_row, ua_data_types.UANodeId):
        data_type_from_row = transform_data_type_to_plain_int(data_type_from_row)

    class_name_from_value = value_from_row.__class__.__name__
    opcua_tools_class_as_str = get_opcua_tools_class_name_from_mapping(
        class_name_from_value, data_type_from_row, row
    )
    if opcua_tools_class_as_str in OPCUA_TOOLS_CLASSES_TO_SKIP:
        row["IsValidValue"] = True
        return row

    if pd.isna(opcua_tools_class_as_str):
        opcua_tools_class_as_str = include_missing_opcua_class_in_mapping_file(
            value_from_row, data_type_from_row
        )

    value_to_check = value_from_row

    if isinstance(value_from_row, ua_data_types.UAListOf):
        first_list_element = value_from_row.value[0]
        value_to_check = first_list_element

    data_type_opcua_tools_class = getattr(ua_data_types, opcua_tools_class_as_str)
    does_value_match_data_type = isinstance(value_to_check, data_type_opcua_tools_class)

    row["IsValidValue"] = does_value_match_data_type
    return row


def transform_data_type_to_plain_int(data_type_from_row: ua_data_types.UANodeId) -> int:
    data_type_as_plain_int = VALUE_MAPPING[
        VALUE_MAPPING["NodeIdDataType"] == f"i={data_type_from_row.value}"
    ].index.values.tolist()[0]
    data_type_from_row = data_type_as_plain_int
    return data_type_from_row


def include_missing_opcua_class_in_mapping_file(
    value_from_row: ua_data_types.UAData, data_type_from_row: int
) -> str:

    if value_from_row.__class__.__name__ == "UAListOf":
        first_list_element = value_from_row.value[0]
        class_name_from_value = first_list_element.__class__.__name__
    else:
        class_name_from_value = value_from_row.__class__.__name__

    VALUE_MAPPING.at[data_type_from_row, "OPCUAToolsClass"] = class_name_from_value

    # Update the mapping file by uncommenting the following line and run the tests:
    # VALUE_MAPPING.to_csv(MAPPING_FILE_PATH, index_label="DataType")

    return class_name_from_value


def get_opcua_tools_class_name_from_mapping(
    class_name_from_value: str, data_type_from_row: int, row: pd.Series
) -> str:
    try:
        opcua_tools_class_as_str = VALUE_MAPPING.iloc[data_type_from_row][
            "OPCUAToolsClass"
        ]
    except IndexError:
        available_opcua_tools_classes = VALUE_MAPPING["OPCUAToolsClass"].dropna().values
        if class_name_from_value in available_opcua_tools_classes:
            opcua_tools_class_as_str = class_name_from_value
        else:
            raise exceptions.ValidationError(
                f"Invalid DataType for row {row.name}: {row['DataType']}"
            )
    return opcua_tools_class_as_str


def validate_values_in_df(df_to_validate: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that the value is valid for the corresponding DataType for all rows in a DataFrame.
    """
    if df_to_validate.empty:
        return df_to_validate

    df_to_validate = df_to_validate.apply(validate_value, axis=1)

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

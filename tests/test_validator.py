import os

import pandas as pd
import pytest
from definitions import get_project_root

from opcua_tools.ua_data_types import UAInt32
from opcua_tools.ua_graph import UAGraph
from opcua_tools.validator import exceptions, value_validator


class TestValidatorFeature:
    def test_validator_raises_error_when_data_type_is_missing_for_uavariable(
        self, invalid_files_root_path
    ):
        path_to_xmls = str(invalid_files_root_path / "missing_data_types")
        ua_graph = UAGraph.from_path(path_to_xmls)

        output_folder = get_project_root() / "tests" / "output"
        output_file_path = str(
            output_folder / "invalid_output_that_eventually_wont_be_created.xml"
        )

        # Creating output folder if it does not exist
        if not os.path.exists(str(output_folder)):
            os.makedirs(str(output_folder))

        with pytest.raises(exceptions.ValidationError):
            ua_graph.write_nodeset(
                output_file_path, "http://prediktor.com/paper_example"
            )

    def test_validate_values_in_df_raises_validation_error(
        self, invalid_files_root_path
    ):
        path_to_xmls = str(invalid_files_root_path / "non_matching_datatype")
        ua_graph = UAGraph.from_path(path_to_xmls)

        output_folder = get_project_root() / "tests" / "output"
        output_file_path = str(
            output_folder / "invalid_output_that_eventually_wont_be_created.xml"
        )

        # Creating output folder if it does not exist
        if not os.path.exists(str(output_folder)):
            os.makedirs(str(output_folder))

        with pytest.raises(exceptions.ValidationError) as e:
            ua_graph.write_nodeset(
                output_file_path, "http://prediktor.com/paper_example"
            )
        exception_obj = e.value
        assert (
            str(exception_obj)
            == "Invalid Value for rows with the following display names: ['FunctionalAspectName']."
        )


class TestValidatorUnit:
    def test_validator_row_is_valid_when_nodeclass_is_not_uavariable(
        self, ua_object_node_row, sample_original_nodes
    ):
        row = value_validator.validate_value(ua_object_node_row, sample_original_nodes)
        assert row["IsValidValue"] is True

    def test_validator_row_is_valid_when_uavariable_has_empty_value(
        self, ua_variable_node_row, sample_original_nodes
    ):
        ua_variable_node_row["Value"] = pd.NA
        row = value_validator.validate_value(
            ua_variable_node_row, sample_original_nodes
        )
        assert row["IsValidValue"] is True

    def test_validator_row_is_invalid_when_opcua_tools_class_name_is_invalid(
        self, ua_variable_node_row, sample_original_nodes
    ):
        ua_variable_node_row["Value"] = 123
        invalid_data_type_id = 99999999999
        ua_variable_node_row["DataType"] = invalid_data_type_id
        with pytest.raises(IndexError):
            value_validator.validate_value(ua_variable_node_row, sample_original_nodes)

    def test_validator_row_is_valid_when_enumeration_is_given(
        self, ua_variable_node_row, sample_original_nodes
    ):
        ua_variable_node_row["Value"] = UAInt32()
        ua_variable_node_row["DataType"] = 1
        row = value_validator.validate_value(
            ua_variable_node_row, sample_original_nodes
        )
        assert row["IsValidValue"] is True

    def test_validator_gets_correct_data_type(
        self, ua_variable_node_row, sample_original_nodes
    ):
        ua_variable_node_row["Value"] = UAInt32()
        sample_nodes_int32_id = 5
        ua_variable_node_row["DataType"] = sample_nodes_int32_id
        row = value_validator.validate_value(
            ua_variable_node_row, sample_original_nodes
        )
        assert row["IsValidValue"] is True

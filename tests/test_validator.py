import os
from unittest import mock

import pandas as pd
import pytest
from definitions import get_project_root

from opcua_tools.json_parser.parse import pre_process_xml_to_json
from opcua_tools.nodeset_parser import get_list_of_xml_files
from opcua_tools.ua_data_types import UABoolean, UAInt32
from opcua_tools.ua_graph import UAGraph
from opcua_tools.validator import exceptions, value_validator


class TestValidatorFeature:
    @mock.patch(
        "opcua_tools.ua_graph.UAGraph._UAGraph__validate_referenced_nodes_exists"
    )
    def test_validator_raises_error_when_data_type_is_missing_for_uavariable(
        self, _, invalid_files_root_path
    ):
        path_to_xmls = str(invalid_files_root_path / "missing_data_types")
        for f in get_list_of_xml_files(path_to_xmls):
            pre_process_xml_to_json(f)
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

    @mock.patch(
        "opcua_tools.ua_graph.UAGraph._UAGraph__validate_referenced_nodes_exists"
    )
    def test_validate_values_in_df_raises_validation_error(
        self, _, invalid_files_root_path
    ):
        path_to_xmls = str(invalid_files_root_path / "non_matching_datatype")
        for f in get_list_of_xml_files(path_to_xmls):
            pre_process_xml_to_json(f)
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
    def test_validator_df_is_valid_when_empty(self, sample_date_type_nodes):
        empty_df = pd.DataFrame({})

        result_df = value_validator.validate_values_in_df(
            empty_df, sample_date_type_nodes
        )

        pd.testing.assert_frame_equal(result_df, empty_df)

    def test_validator_df_is_valid_when_nodeclass_is_not_uavariable(
        self, ua_object_node_df, sample_date_type_nodes
    ):
        ua_object_node_df["NodeClass"] = "UAObject"

        result_df = value_validator.validate_values_in_df(
            ua_object_node_df, sample_date_type_nodes
        )

        pd.testing.assert_frame_equal(result_df, ua_object_node_df)

    def test_validator_df_is_valid_when_uavariable_has_empty_value(
        self, ua_object_node_df, sample_date_type_nodes
    ):
        result_df = value_validator.validate_values_in_df(
            ua_object_node_df, sample_date_type_nodes
        )

        pd.testing.assert_frame_equal(result_df, ua_object_node_df)

    def test_validator_row_is_invalid_when_opcua_tools_class_name_is_invalid(
        self, ua_object_node_df, sample_date_type_nodes
    ):
        ua_object_node_df["Value"] = UABoolean(value=True)
        invalid_data_type_id = 1
        ua_object_node_df["DataType"] = invalid_data_type_id

        with pytest.raises(exceptions.ValidationError):
            value_validator.validate_values_in_df(
                ua_object_node_df, sample_date_type_nodes
            )

    def test_validator_row_is_valid_when_enumeration_is_given(
        self, ua_object_node_df, sample_date_type_nodes
    ):
        ua_object_node_df["Value"] = UAInt32()
        ua_object_node_df["DataType"] = 0

        result_df = value_validator.validate_values_in_df(
            ua_object_node_df, sample_date_type_nodes
        )

        pd.testing.assert_frame_equal(result_df, ua_object_node_df)

    def test_validator_gets_correct_data_type(
        self, ua_object_node_df, sample_date_type_nodes
    ):
        ua_object_node_df["Value"] = UAInt32()
        sample_nodes_int32_id = 1
        ua_object_node_df["DataType"] = sample_nodes_int32_id

        result_df = value_validator.validate_values_in_df(
            ua_object_node_df, sample_date_type_nodes
        )

        pd.testing.assert_frame_equal(result_df, ua_object_node_df)

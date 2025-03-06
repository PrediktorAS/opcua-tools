import decimal
import json
from datetime import datetime

import pandas as pd
import pytest

from opcua_tools.ua_data_types import (
    NodeIdType,
    UABoolean,
    UAByte,
    UAByteString,
    UADateTime,
    UADouble,
    UAEngineeringUnits,
    UAEUInformation,
    UAEURange,
    UAExtensionObject,
    UAFloat,
    UAInt16,
    UAInt32,
    UAInt64,
    UAListOf,
    UALocalizedText,
    UANodeId,
    UAQualifiedName,
    UARange,
    UASByte,
    UAString,
    UAStructure,
    UAUInt16,
    UAUInt32,
    UAUInt64,
    UAVariant,
    UAXMLElement,
    VariantType,
)


def test_ua_integer_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAInt16(value="foo")
    with pytest.raises(TypeError):
        UAUInt16(value="foo")


def test_ua_unsigned_integer_creation_with_negative_integer():
    with pytest.raises(ValueError):
        UAUInt16(value=-42)
    with pytest.raises(ValueError):
        UAUInt32(value=-43)
    with pytest.raises(ValueError):
        UAUInt64(value=-1)


def test_ua_unsigned_integer_creation_with_float_point_number():
    with pytest.raises(TypeError):
        UAUInt16(float(42.2))
    with pytest.raises(TypeError):
        UAUInt16(decimal(42.2))
    with pytest.raises(TypeError):
        UAUInt32(float(42.2))
    with pytest.raises(TypeError):
        UAUInt32(decimal(42.2))
    with pytest.raises(TypeError):
        UAUInt64(float(42.2))
    with pytest.raises(TypeError):
        UAUInt64(decimal(42.2))


def test_ua_signed_integer_creation_with_float_point_number():
    with pytest.raises(TypeError):
        UAInt16(float(42.2))
    with pytest.raises(TypeError):
        UAInt16(decimal(42.2))
    with pytest.raises(TypeError):
        UAInt32(float(42.2))
    with pytest.raises(TypeError):
        UAInt32(decimal(42.2))
    with pytest.raises(TypeError):
        UAInt64(float(42.2))
    with pytest.raises(TypeError):
        UAInt64(decimal(42.2))


def test_ua_unsigned_integer_creation_with_none_value():
    ua_uint16 = UAUInt16(None)
    assert ua_uint16.value is None
    ua_uint32 = UAUInt32(None)
    assert ua_uint32.value is None
    ua_uint64 = UAUInt64(None)
    assert ua_uint64.value is None


def test_ua_signed_integer_creation_with_none_value():
    ua_int16 = UAInt16(None)
    assert ua_int16.value is None
    ua_int32 = UAInt32(None)
    assert ua_int32.value is None
    ua_int64 = UAInt64(None)
    assert ua_int64.value is None


def test_ua_integer_xml_encode_with_value():
    ua_int16 = UAInt16(value=42)
    ua_uint16 = UAUInt16(value=42)
    ua_int32 = UAInt32(value=42)
    ua_uint32 = UAUInt32(value=42)
    ua_int64 = UAInt64(value=42)
    ua_uint64 = UAUInt64(value=42)
    assert ua_int16.xml_encode(include_xmlns=False) == "<Int16>42</Int16>"
    assert ua_uint16.xml_encode(include_xmlns=False) == "<UInt16>42</UInt16>"
    assert ua_int32.xml_encode(include_xmlns=False) == "<Int32>42</Int32>"
    assert ua_uint32.xml_encode(include_xmlns=False) == "<UInt32>42</UInt32>"
    assert ua_int64.xml_encode(include_xmlns=False) == "<Int64>42</Int64>"
    assert ua_uint64.xml_encode(include_xmlns=False) == "<UInt64>42</UInt64>"

    assert (
        ua_int16.xml_encode(include_xmlns=True)
        == '<Int16 xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42</Int16>'
    )
    assert (
        ua_uint16.xml_encode(include_xmlns=True)
        == '<UInt16 xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42</UInt16>'
    )
    assert (
        ua_int32.xml_encode(include_xmlns=True)
        == '<Int32 xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42</Int32>'
    )
    assert (
        ua_uint32.xml_encode(include_xmlns=True)
        == '<UInt32 xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42</UInt32>'
    )
    assert (
        ua_int64.xml_encode(include_xmlns=True)
        == '<Int64 xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42</Int64>'
    )
    assert (
        ua_uint64.xml_encode(include_xmlns=True)
        == '<UInt64 xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42</UInt64>'
    )


def test_ua_integer_json_encode_with_value():
    ua_int16 = UAInt16(value=42)
    ua_uint16 = UAUInt16(value=42)
    ua_int32 = UAInt32(value=42)
    ua_uint32 = UAUInt32(value=42)
    ua_int64 = UAInt64(value=42)
    ua_uint64 = UAUInt64(value=42)
    assert ua_int16.json_encode() == "42"
    assert ua_uint16.json_encode() == "42"
    assert ua_int32.json_encode() == "42"
    assert ua_uint32.json_encode() == "42"
    assert ua_int64.json_encode() == '"42.0"'
    assert ua_uint64.json_encode() == '"42.0"'


def test_ua_integer_json_encode_with_none_value():
    ua_int16 = UAInt16(None)
    ua_uint16 = UAUInt16(None)
    ua_int32 = UAInt32(None)
    ua_uint32 = UAUInt32(None)
    ua_int64 = UAInt64(None)
    ua_uint64 = UAUInt64(None)
    assert ua_int16.json_encode() == None
    assert ua_uint16.json_encode() == None
    assert ua_int32.json_encode() == None
    assert ua_uint32.json_encode() == None
    assert ua_int64.json_encode() == None
    assert ua_uint64.json_encode() == None


def test_ua_floating_point_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAFloat(value="foo")
    with pytest.raises(TypeError):
        UADouble(value="foo")


def test_ua_floating_point_creation_casting_from_integer():
    ua_float = UAFloat(value=42)
    assert ua_float.value == float(42)
    ua_double = UADouble(value=42)
    assert ua_double.value == float(42)


def test_ua_floating_point_creation_with_none_value():
    ua_float = UAFloat(None)
    assert isinstance(ua_float.value, pd._libs.missing.NAType)
    ua_double = UADouble(None)
    assert isinstance(ua_double.value, pd._libs.missing.NAType)


def test_ua_floating_point_xml_encode_with_value():
    ua_float = UAFloat(value=42.0)
    ua_double = UADouble(value=42.0)
    assert ua_float.xml_encode(include_xmlns=False) == "<Float>42.0</Float>"
    assert ua_double.xml_encode(include_xmlns=False) == "<Double>42.0</Double>"

    assert (
        ua_float.xml_encode(include_xmlns=True)
        == '<Float xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42.0</Float>'
    )
    assert (
        ua_double.xml_encode(include_xmlns=True)
        == '<Double xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">42.0</Double>'
    )


def test_ua_floating_point_json_encode_with_value():
    ua_float = UAFloat(value=42.0)
    ua_double = UADouble(value=42.0)
    assert ua_float.json_encode() == "42.0"
    assert ua_double.json_encode() == "42.0"

    ua_float = UAFloat(value=float("inf"))
    ua_double = UADouble(value=float("inf"))
    assert ua_float.json_encode() == '"Infinity"'
    assert ua_double.json_encode() == '"Infinity"'

    ua_float = UAFloat(value=float("-inf"))
    ua_double = UADouble(value=float("-inf"))
    assert ua_float.json_encode() == '"-Infinity"'
    assert ua_double.json_encode() == '"-Infinity"'

    ua_float = UAFloat(value=float("nan"))
    ua_double = UADouble(value=float("nan"))
    assert ua_float.json_encode() == '"NaN"'
    assert ua_double.json_encode() == '"NaN"'


def test_ua_floating_point_json_encode_with_none_value():
    ua_float = UAFloat(None)
    ua_double = UADouble(None)
    assert ua_float.json_encode() == None
    assert ua_double.json_encode() == None


def test_ua_string_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAString(value=42)


def test_ua_string_creation_with_none_value():
    ua_string = UAString(None)
    assert isinstance(ua_string.value, pd._libs.missing.NAType)


def test_ua_string_should_be_pd_na_if_empty_one_given():
    ua_string = UAString("")

    assert isinstance(ua_string.value, pd._libs.missing.NAType)


def test_ua_string_xml_encode():
    ua_string = UAString("Hello, World!")
    assert ua_string.xml_encode(include_xmlns=False) == "<String>Hello, World!</String>"
    assert (
        ua_string.xml_encode(include_xmlns=True)
        == '<String xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">Hello, World!</String>'
    )

    assert UAString("The and symbol: & is escaped").xml_encode(include_xmlns=False) == (
        "<String>The and symbol: &amp; is escaped</String>"
    )


def test_ua_string_json_encode():
    # Test case 1: Value is None
    ua_string = UAString(None)
    assert ua_string.json_encode() is None

    # Test case 2: Value is not None
    ua_string = UAString("Hello, World!")
    expected_result = '"Hello, World!"'
    assert ua_string.json_encode() == expected_result

    # Test case 3: Value contains double quotes
    ua_string = UAString('This "quote" is escaped')
    expected_result = json.dumps('This "quote" is escaped')
    assert ua_string.json_encode() == expected_result

    # Test case 4: Value contains backslashes
    ua_string = UAString("C:\\Program Files\\")
    expected_result = json.dumps("C:\\Program Files\\")
    assert ua_string.json_encode() == expected_result

    # Test case 5: Value contains special characters
    ua_string = UAString("<html> &amp; </html>")
    expected_result = json.dumps("<html> &amp; </html>")
    assert ua_string.json_encode() == expected_result

    # Test case 6: Value contains Unicode characters
    ua_string = UAString("Résumé")
    expected_result = '"Résumé"'
    assert ua_string.json_encode() == expected_result


def test_ua_datetime_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UADateTime(value="foo")
    with pytest.raises(TypeError):
        UADateTime(value=None)


def test_ua_datetime_creation_with_value():
    # initializing datetime object with python datetime object
    datetime_obj = datetime(2021, 1, 1, 0, 0, 0)
    ua_datetime = UADateTime(value=datetime_obj)
    assert ua_datetime.value == datetime_obj


def test_ua_datetime_xml_encode_with_value():
    ua_datetime = UADateTime(value=datetime(2021, 1, 1, 0, 0, 0))
    expected_xml = "<DateTime>2021-01-01T00:00:00.000000Z</DateTime>"
    actual_xml = ua_datetime.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml


def test_ua_datetime_json_encode_with_value():
    # initializing datetime object with python datetime object
    ua_datetime = UADateTime(value=pd.Timestamp("2021-01-01 00:00:00"))
    expected_json = '"2021-01-01T00:00:00.000000Z"'
    actual_json = ua_datetime.json_encode()
    assert actual_json == expected_json


def test_ua_byte_string_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAByteString(value=42)


def test_ua_byte_string_creation_with_none_value():
    ua_byte_string = UAByteString(None)
    assert isinstance(ua_byte_string.value, pd._libs.missing.NAType)


def test_ua_byte_string_xml_encode():
    ua_byte_string = UAByteString(b"Hello, world!")
    assert (
        ua_byte_string.xml_encode(include_xmlns=False)
        == "<ByteString>SGVsbG8sIHdvcmxkIQ==</ByteString>"
    )
    assert (
        ua_byte_string.xml_encode(include_xmlns=True)
        == '<ByteString xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">SGVsbG8sIHdvcmxkIQ==</ByteString>'
    )


def test_ua_byte_string_json_encode():
    # Test case 1: Value is None
    obj = UAByteString(None)
    assert obj.json_encode() is None

    # Test case 2: Value is not None
    value = b"Hello, world!"
    obj = UAByteString(value)
    # expected_output = json.dumps(b64encode(value).decode("utf-8"), ensure_ascii=False)
    expected_output = '"SGVsbG8sIHdvcmxkIQ=="'
    actual_output = obj.json_encode()
    assert actual_output == expected_output


def test_ua_boolean_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UABoolean(value=42)
    with pytest.raises(TypeError):
        UABoolean(value="Some string")


def test_ua_boolean_creation_with_none_value():
    ua_boolean = UABoolean(None)
    assert ua_boolean.value is None


def test_ua_boolean_json_encode_with_value():
    ua_boolean = UABoolean(value=True)
    assert ua_boolean.json_encode() == "true"
    ua_boolean = UABoolean(value=False)
    assert ua_boolean.json_encode() == "false"


def test_ua_boolean_xml_encode_with_value():
    ua_boolean = UABoolean(value=True)
    assert ua_boolean.xml_encode(include_xmlns=False) == "<Boolean>true</Boolean>"
    ua_boolean = UABoolean(value=False)
    assert ua_boolean.xml_encode(include_xmlns=False) == "<Boolean>false</Boolean>"
    assert (
        ua_boolean.xml_encode(include_xmlns=True)
        == '<Boolean xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">false</Boolean>'
    )


def test_ua_boolean_json_encode_with_none_value():
    ua_boolean = UABoolean(None)
    assert ua_boolean.json_encode() == None


def test_ua_xml_element_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAXMLElement(value=42)
    with pytest.raises(TypeError):
        UAXMLElement(value=None)


def test_ua_xml_element_creation_with_value():
    ua_xml_element = UAXMLElement(value="<foo>bar</foo>")
    assert ua_xml_element.value == "<foo>bar</foo>"


def test_ua_xml_element_xml_encode_with_value():
    ua_xml_element = UAXMLElement(value="<foo>bar</foo>")
    expected_xml = "<foo>bar</foo>"
    actual_xml = ua_xml_element.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    # Value contains special characters
    ua_xml_element = UAXMLElement("<html> &amp; </html>")
    expected_result = "<html> &amp; </html>"
    assert ua_xml_element.xml_encode(include_xmlns=False) == expected_result


def test_ua_xml_element_json_encode_with_value():
    ua_xml_element = UAXMLElement(value="<foo>bar</foo>")
    expected_json = '"<foo>bar</foo>"'
    actual_json = ua_xml_element.json_encode()
    assert actual_json == expected_json

    # Value contains special characters
    ua_string = UAXMLElement("<html> &amp; </html>")
    expected_result = json.dumps("<html> &amp; </html>")
    assert ua_string.json_encode() == expected_result


def test_ua_node_id_creation_with_incorrect_type():
    with pytest.raises(ValueError):
        UANodeId(value=42, namespace=0, nodeid_type="foo")
    with pytest.raises(TypeError):
        UANodeId(value="foo", namespace=0, nodeid_type=0)
    with pytest.raises(TypeError):
        UANodeId(value="-21", namespace=0, nodeid_type=0)
    with pytest.raises(TypeError):
        UANodeId(value=42, namespace="foo", nodeid_type=1)
    with pytest.raises(ValueError):
        UANodeId(value="foo", namespace=1, nodeid_type="q")


def test_ua_node_id_creation_with_correct_values():
    ua_node_id = UANodeId(value="42", namespace=0, nodeid_type=0)
    assert ua_node_id.value == "42"
    assert ua_node_id.namespace == 0
    assert ua_node_id.nodeid_type == NodeIdType.NUMERIC
    assert isinstance(ua_node_id.nodeid_type, NodeIdType)

    ua_node_id = UANodeId(value="42", namespace=0, nodeid_type="i")
    assert ua_node_id.value == "42"
    assert ua_node_id.namespace == 0
    assert ua_node_id.nodeid_type == NodeIdType.NUMERIC
    assert isinstance(ua_node_id.nodeid_type, NodeIdType)

    ua_node_id = UANodeId(
        value="ParentBrowseName.MyBrowseName", namespace=0, nodeid_type=1
    )
    assert ua_node_id.value == "ParentBrowseName.MyBrowseName"
    assert ua_node_id.namespace == 0
    assert ua_node_id.nodeid_type == NodeIdType.STRING
    assert isinstance(ua_node_id.nodeid_type, NodeIdType)

    ua_node_id = UANodeId(
        value="ParentBrowseName.MyBrowseName", namespace=0, nodeid_type="s"
    )
    assert ua_node_id.value == "ParentBrowseName.MyBrowseName"
    assert ua_node_id.namespace == 0
    assert ua_node_id.nodeid_type == NodeIdType.STRING
    assert isinstance(ua_node_id.nodeid_type, NodeIdType)


def test_ua_node_id_xml_encode_with_value():
    ua_node_id = UANodeId(value="42", namespace=0, nodeid_type=0)
    expected_xml = "<Identifier>i=42</Identifier>"
    actual_xml = ua_node_id.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    ua_node_id = UANodeId(value="42", namespace=0, nodeid_type=0)
    expected_xml = '<Identifier xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">i=42</Identifier>'
    actual_xml = ua_node_id.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_node_id_json_encode_with_value():
    ua_node_id = UANodeId(value="42", namespace=0, nodeid_type=0)
    expected_json = '{"Id":42}'
    actual_json = ua_node_id.json_encode()
    assert actual_json == expected_json

    ua_node_id = UANodeId(value="42", namespace=1, nodeid_type=0)
    expected_json = '{"Namespace":1,"Id":42}'
    actual_json = ua_node_id.json_encode()
    assert actual_json == expected_json

    ua_node_id = UANodeId(value="MyNodeIdentifier", namespace=1, nodeid_type=1)
    expected_json = '{"Namespace":1,"IdType":1,"Id":"MyNodeIdentifier"}'
    actual_json = ua_node_id.json_encode()
    assert actual_json == expected_json


def test_ua_qualified_name_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAQualifiedName(name=42, namespace_index=0)
    with pytest.raises(TypeError):
        UAQualifiedName(name="foo", namespace_index="bar")
    with pytest.raises(ValueError):
        UAQualifiedName(name="foo", namespace_index=-1)


def test_ua_qualified_name_creation_with_correct_values():
    ua_qualified_name = UAQualifiedName(name="foo", namespace_index=0)
    assert ua_qualified_name.name == "foo"
    assert ua_qualified_name.namespace_index == 0

    ua_qualified_name = UAQualifiedName(name="foo", namespace_index=1)
    assert ua_qualified_name.name == "foo"
    assert ua_qualified_name.namespace_index == 1


def test_ua_qualified_name_xml_encode_with_value():
    ua_qualified_name = UAQualifiedName(name="foo", namespace_index=0)
    expected_xml = "<QualifiedName><NamespaceIndex>0</NamespaceIndex><Name>foo</Name></QualifiedName>"
    actual_xml = ua_qualified_name.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    ua_qualified_name = UAQualifiedName(name="foo", namespace_index=1)
    expected_xml = '<QualifiedName xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><NamespaceIndex>1</NamespaceIndex><Name>foo</Name></QualifiedName>'
    actual_xml = ua_qualified_name.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_qualified_name_json_encode_with_value():
    ua_qualified_name = UAQualifiedName(name="foo", namespace_index=0)
    expected_json = '{"Name":"foo"}'
    actual_json = ua_qualified_name.json_encode()
    assert actual_json == expected_json

    ua_qualified_name = UAQualifiedName(name="foo", namespace_index=1)
    expected_json = '{"Name":"foo","Uri":1}'
    actual_json = ua_qualified_name.json_encode()
    assert actual_json == expected_json


def test_ua_localized_text_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UALocalizedText(text=42, locale="en-US")
    with pytest.raises(TypeError):
        UALocalizedText(text="foo", locale=42)
    with pytest.raises(ValueError):
        UALocalizedText(text="foo", locale="foobarillo")


def test_ua_localized_text_creation_with_correct_values():
    ua_localized_text = UALocalizedText(text=None, locale=None)
    assert ua_localized_text.text is None
    assert ua_localized_text.locale is None

    ua_localized_text = UALocalizedText(text="foo", locale="en-US")
    assert ua_localized_text.text == "foo"
    assert ua_localized_text.locale == "en-US"

    ua_localized_text = UALocalizedText(text="foo", locale="de-DE")
    assert ua_localized_text.text == "foo"
    assert ua_localized_text.locale == "de-DE"


def test_ua_localized_text_is_valid_locale_with_different_locales():
    valid_locales = [
        "en-US",
        "de-DE",
        "fr-FR",
        "es-ES",
        "zh-CN",
        "zh-TW",
        "ja",
        "ko",
        "itn",
        "pt-BRA_kls",
        "pt-BRr-kls.ks",
        "pt-BRr-kls.ksslbei",
    ]
    for locale in valid_locales:
        assert UALocalizedText.is_valid_locale(locale) is True

    invalid_locales = [
        "foobarillo",
        "engl",
        "dech",
        "fr--FR",
        "es__ES",
        "zh-CNNR",
        "zh_CNNR",
    ]
    for locale in invalid_locales:
        assert UALocalizedText.is_valid_locale(locale) is False


def test_ua_localized_text_xml_encoding_with_value():
    ua_localized_text = UALocalizedText(text="foo", locale="en-US")
    expected_xml = (
        "<LocalizedText><Locale>en-US</Locale><Text>foo</Text></LocalizedText>"
    )
    actual_xml = ua_localized_text.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    ua_localized_text = UALocalizedText(text="foo", locale="en-US")
    expected_xml = '<LocalizedText xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><Locale>en-US</Locale><Text>foo</Text></LocalizedText>'
    actual_xml = ua_localized_text.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_localized_text_json_encoding_with_none():
    ua_localized_text = UALocalizedText(text=None, locale=None)
    expected_json = '{"Text":""}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json

    ua_localized_text = UALocalizedText(text=None, locale="en-US")
    expected_json = '{"Text":"","Locale":"en-US"}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json


def test_ua_localized_text_json_encoding_with_pd_na():
    ua_localized_text = UALocalizedText(text=pd.NA, locale=pd.NA)
    expected_json = '{"Text":""}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json

    ua_localized_text = UALocalizedText(text=pd.NA, locale="en-US")
    expected_json = '{"Text":"","Locale":"en-US"}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json


def test_ua_localized_text_json_encoding_with_input_locale_as_pd_na():
    ua_localized_text = UALocalizedText(text="Some text", locale=pd.NA)
    expected_json = '{"Text":"Some text"}'
    actual_json = ua_localized_text.json_encode(input_locale=pd.NA)
    assert actual_json == expected_json


def test_ua_localized_text_json_encoding_with_locale_as_pd_na():
    ua_localized_text = UALocalizedText(text="Some text", locale=pd.NA)
    expected_json = '{"Text":"Some text"}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json


def test_ua_localized_text_json_encode_with_input_locale():
    # Testing that input_locale overrides the locale if there
    ua_localized_text = UALocalizedText(text="foo", locale="en-US")
    expected_json = '{"Text":"foo","Locale":"de-DE"}'
    actual_json = ua_localized_text.json_encode(input_locale="de-DE")
    assert actual_json == expected_json

    # Testing that input_locale overrides the locale if None
    ua_localized_text = UALocalizedText(text="foo", locale=None)
    expected_json = '{"Text":"foo","Locale":"de-DE"}'
    actual_json = ua_localized_text.json_encode(input_locale="de-DE")
    assert actual_json == expected_json


def test_ua_localized_text_json_encode_with_value():
    ua_localized_text = UALocalizedText(text="foo", locale="en-US")
    expected_json = '{"Text":"foo","Locale":"en-US"}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json

    ua_localized_text = UALocalizedText(text="foo", locale="de-DE")
    expected_json = '{"Text":"foo","Locale":"de-DE"}'
    actual_json = ua_localized_text.json_encode()
    assert actual_json == expected_json


def test_ua_extension_object_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAExtensionObject(
            body=UAString("foo"),
            type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
        )
    with pytest.raises(TypeError):
        UAExtensionObject(
            body=UAStructure(UAString("foo")),
            type_nodeid=45,
        )


def test_ua_extension_object_creation_with_correct_values():
    ua_extension_object = UAExtensionObject(
        body=UAStructure(UAString("foo")),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
    )
    assert ua_extension_object.body == UAStructure(UAString("foo"))
    assert ua_extension_object.type_nodeid == UANodeId(
        namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1
    )

    ua_extension_object = UAExtensionObject(
        body=UAStructure(UABoolean(True)),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
    )
    assert ua_extension_object.body == UAStructure(UABoolean(True))
    assert ua_extension_object.type_nodeid == UANodeId(
        namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1
    )


def test_ua_extention_object_xml_encode():
    ua_extension_object = UAExtensionObject(
        body=UAStructure(UAString("foo")),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
    )
    expected_xml = "<ExtensionObject><TypeId><Identifier>i=1</Identifier></TypeId><Body><String>foo</String></Body></ExtensionObject>"
    actual_xml = ua_extension_object.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    ua_extension_object = UAExtensionObject(
        body=UAStructure(UABoolean(True)),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
    )
    actual_xml = ua_extension_object.xml_encode(include_xmlns=True)
    expected_xml = '<ExtensionObject xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><TypeId><Identifier>i=1</Identifier></TypeId><Body><Boolean>true</Boolean></Body></ExtensionObject>'
    assert actual_xml == expected_xml


def test_ua_extension_object_json_encode():
    ua_extension_object = UAExtensionObject(
        body=UAStructure(UAString("foo")),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
    )
    expected_json = '{"TypeId":{"Id":1},"Body":"foo"}'
    actual_json = ua_extension_object.json_encode()
    assert actual_json == expected_json

    ua_extension_object = UAExtensionObject(
        body=UAStructure(UABoolean(True)),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=1),
    )
    expected_json = '{"TypeId":{"Id":1},"Body":true}'
    actual_json = ua_extension_object.json_encode()
    assert actual_json == expected_json


def test_ua_variant_creation_with_incorrect_type():
    with pytest.raises(TypeError):
        UAVariant(value="foo", type="int")
    with pytest.raises(TypeError):
        UAVariant(value=42, type=42)
    with pytest.raises(TypeError):
        UAVariant(value="foo", type="foobarillo")

    with pytest.raises(TypeError):
        UAVariant(value=None, type=None)
    with pytest.raises(TypeError):
        UAVariant(value=42, type=VariantType.Int16)
    with pytest.raises(TypeError):
        UAVariant(value="somestring", type=VariantType.String)


def test_ua_variant_creation_with_correct_values():
    ua_variant = UAVariant(value=None)
    assert ua_variant.value is None
    assert ua_variant.type is VariantType.Null

    ua_variant = UAVariant(value=UAUInt16(3), type=VariantType.UInt16)
    assert ua_variant.value == UAUInt16(3)
    assert ua_variant.type is VariantType.UInt16

    ua_variant = UAVariant(value=UAInt16(-3), type=VariantType.Int16)
    assert ua_variant.value == UAInt16(-3)
    assert ua_variant.type is VariantType.Int16

    ua_variant = UAVariant(value=UAInt32(-3), type=VariantType.Int32)
    assert ua_variant.value == UAInt32(-3)
    assert ua_variant.type is VariantType.Int32

    ua_variant = UAVariant(value=UAUInt32(3), type=VariantType.UInt32)
    assert ua_variant.value == UAUInt32(3)
    assert ua_variant.type is VariantType.UInt32

    ua_variant = UAVariant(value=UAUInt64(0), type=VariantType.UInt64)
    assert ua_variant.value == UAUInt64(0)
    assert ua_variant.type is VariantType.UInt64

    ua_variant = UAVariant(value=UAInt64(0), type=VariantType.Int64)
    assert ua_variant.value == UAInt64(0)
    assert ua_variant.type is VariantType.Int64

    ua_variant = UAVariant(value=UAString("foo"), type=VariantType.String)
    assert ua_variant.value == UAString("foo")
    assert ua_variant.type is VariantType.String

    ua_variant = UAVariant(value=UABoolean(True), type=VariantType.Boolean)
    assert ua_variant.value == UABoolean(True)
    assert ua_variant.type is VariantType.Boolean

    ua_variant = UAVariant(value=UAByteString(b"foo"), type=VariantType.ByteString)
    assert ua_variant.value == UAByteString(b"foo")
    assert ua_variant.type is VariantType.ByteString

    ua_variant = UAVariant(value=UAFloat(3.14), type=VariantType.Float)
    assert ua_variant.value == UAFloat(3.14)
    assert ua_variant.type is VariantType.Float

    ua_variant = UAVariant(value=UADouble(3.14), type=VariantType.Double)
    assert ua_variant.value == UADouble(3.14)
    assert ua_variant.type is VariantType.Double

    ua_variant = UAVariant(
        value=UADateTime(value=pd.Timestamp("2021-01-01 00:00:00")),
        type=VariantType.DateTime,
    )
    assert ua_variant.value == UADateTime(value=pd.Timestamp("2021-01-01 00:00:00"))
    assert ua_variant.type is VariantType.DateTime

    # ua_variant = UAVariant(value=UAGuid("3.14"), type=VariantType.Guid)
    # assert ua_variant.value == UAGuid("3.14")
    # assert ua_variant.type is VariantType.Guid

    ua_variant = UAVariant(
        value=UALocalizedText(text="foo", locale="en-US"),
        type=VariantType.LocalizedText,
    )
    assert ua_variant.value == UALocalizedText("foo", "en-US")
    assert ua_variant.type is VariantType.LocalizedText

    ua_variant = UAVariant(
        value=UAQualifiedName(name="foo", namespace_index=1),
        type=VariantType.QualifiedName,
    )
    assert ua_variant.value == UAQualifiedName(name="foo", namespace_index=1)
    assert ua_variant.type is VariantType.QualifiedName

    # ua_variant = UAVariant(value=UAStatusCode(0), type=VariantType.StatusCode)
    # assert ua_variant.value == UAStatusCode(0)
    # assert ua_variant.type is VariantType.StatusCode

    ua_variant = UAVariant(value=UAByte(0), type=VariantType.Byte)
    assert ua_variant.value == UAByte(0)
    assert ua_variant.type is VariantType.Byte

    ua_variant = UAVariant(value=UASByte(0), type=VariantType.SByte)
    assert ua_variant.value == UASByte(0)
    assert ua_variant.type is VariantType.SByte

    # ua_variant = UAVariant(value=UADataValue(0), type=VariantType.DataValue)
    # assert ua_variant.value == UADataValue(0)
    # assert ua_variant.type is VariantType.DataValue

    # ua_variant = UAVariant(value=UAExpandedNodeId(0), type=VariantType.ExpandedNodeId)
    # assert ua_variant.value == UAExpandedNodeId(0)
    # assert ua_variant.type is VariantType.ExpandedNodeId

    # ua_variant = UAVariant(value=UAStatusCode(0), type=VariantType.Variant)
    # assert ua_variant.value == UAStatusCode(0)
    # assert ua_variant.type is VariantType.Variant


def test_ua_variant_creation_with_correct_values_without_setting_type():
    ua_variant = UAVariant(value=UAUInt16(3))
    assert ua_variant.value == UAUInt16(3)
    assert ua_variant.type is VariantType.UInt16

    ua_variant = UAVariant(value=UAString("foo"))
    assert ua_variant.value == UAString("foo")
    assert ua_variant.type is VariantType.String

    ua_variant = UAVariant(value=UABoolean(True))
    assert ua_variant.value == UABoolean(True)
    assert ua_variant.type is VariantType.Boolean

    ua_variant = UAVariant(value=UAByteString(b"foo"))
    assert ua_variant.value == UAByteString(b"foo")
    assert ua_variant.type is VariantType.ByteString

    ua_variant = UAVariant(value=UAFloat(3.14))
    assert ua_variant.value == UAFloat(3.14)
    assert ua_variant.type is VariantType.Float

    ua_variant = UAVariant(value=UADouble(3.14))
    assert ua_variant.value == UADouble(3.14)
    assert ua_variant.type is VariantType.Double


def test_ua_variant_creation_with_different_range_objects():
    # Setting a UAExtensionObject for EURange
    ua_extension_object = UAExtensionObject(
        body=UAStructure(UAEURange(low=0, high=100)),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value="885"),
    )
    ua_variant = UAVariant(ua_extension_object, type=VariantType.ExtensionObject)
    assert ua_variant.value == ua_extension_object
    assert ua_variant.type is VariantType.ExtensionObject

    # Setting a UAExtensionObject with UAStructure with UARange object
    ua_extension_object = UAExtensionObject(
        body=UAStructure(UARange(low=0, high=100)),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value="885"),
    )
    ua_variant = UAVariant(ua_extension_object, type=VariantType.ExtensionObject)
    assert ua_variant.value == ua_extension_object
    assert ua_variant.type is VariantType.ExtensionObject

    # Setting a UAExtensionObject from EURange object
    ua_eu_range = UAEURange(low=0, high=100)
    ua_extension_object = UAExtensionObject(
        body=UAStructure(ua_eu_range),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value="885"),
    )
    ua_variant = UAVariant(ua_extension_object, type=VariantType.ExtensionObject)
    assert ua_variant.value == ua_extension_object
    assert ua_variant.type is VariantType.ExtensionObject


def test_ua_variant_creation_with_different_engineering_unit_objects():
    ua_extension_object_value = UAExtensionObject(
        body=UAStructure(
            UAEUInformation(
                display_name=UALocalizedText("foo", "en-US"),
                description=UALocalizedText("bar", "en-US"),
                unit_id=42,
                namespace_uri="www.mynamespace.com/",
            ),
        ),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value="887"),
    )
    ua_variant = UAVariant(
        value=ua_extension_object_value,
        type=VariantType.ExtensionObject,
    )
    assert ua_variant.value == ua_extension_object_value
    assert ua_variant.type is VariantType.ExtensionObject

    ua_engingeering_units = UAEngineeringUnits(
        display_name=UALocalizedText("foo", "en-US"),
        description=UALocalizedText("bar", "en-US"),
        unit_id=42,
        namespace_uri="www.mynamespace.com/",
    )
    ua_extension_object = UAExtensionObject(
        body=UAStructure(ua_engingeering_units),
        type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value="887"),
    )
    ua_variant = UAVariant(
        value=ua_extension_object,
        type=VariantType.ExtensionObject,
    )
    assert ua_variant.value == ua_variant.value
    assert ua_variant.type is VariantType.ExtensionObject


def test_ua_variant_xml_encode_with_value():
    ua_variant = UAVariant(value=UAString("MyStringaling"), type=VariantType.String)
    actual_xml = ua_variant.xml_encode(include_xmlns=False)
    expected_xml = "<Variant><Value><String>MyStringaling</String></Value></Variant>"
    assert actual_xml == expected_xml

    ua_variant = UAVariant(value=UAFloat(3.14), type=VariantType.Float)
    expected_xml = (
        '<Variant xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">'
        '<Value><Float xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd">3.14</Float></Value>'
        "</Variant>"
    )
    actual_xml = ua_variant.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_variant_json_encode_with_value():
    ua_variant = UAVariant(value=UAFloat(3.14), type=VariantType.Float)
    expected_json = '{"Type":10,"Body":3.14}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UAString("foo"), type=VariantType.String)
    expected_json = '{"Type":12,"Body":"foo"}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UABoolean(True), type=VariantType.Boolean)
    expected_json = '{"Type":1,"Body":true}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UAByte(0x01), type=VariantType.Byte)
    expected_json = '{"Type":3,"Body":1}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UASByte(0), type=VariantType.SByte)
    expected_json = '{"Type":2,"Body":0}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UAInt16(153), type=VariantType.Int16)
    expected_json = '{"Type":4,"Body":153}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UAInt32(153), type=VariantType.Int32)
    expected_json = '{"Type":6,"Body":153}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UAInt64(153), type=VariantType.Int64)
    expected_json = '{"Type":8,"Body":"153.0"}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UAUInt64(153), type=VariantType.UInt64)
    expected_json = '{"Type":9,"Body":"153.0"}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(value=UADouble(3.14), type=VariantType.Double)
    expected_json = '{"Type":11,"Body":3.14}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(
        value=UADateTime(value=pd.Timestamp("2021-01-01 00:00:00")),
        type=VariantType.DateTime,
    )
    expected_json = '{"Type":13,"Body":"2021-01-01T00:00:00.000000Z"}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    # ua_variant = UAVariant(
    #     value=UAGuid("12345678-9ABC-DEF0-1234-56789ABCDEF0"), type=VariantType.Guid
    # )
    # expected_json = '{"Type":14,"Body":"12345678-9ABC-DEF0-1234-56789ABCDEF0"}'
    # actual_json = ua_variant.json_encode()
    # assert actual_json == expected_json

    ua_variant = UAVariant(value=UAByteString(b"foo"), type=VariantType.ByteString)
    expected_json = '{"Type":15,"Body":"Zm9v"}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(
        value=UAXMLElement("<foo>bar</foo>"), type=VariantType.XmlElement
    )
    expected_json = '{"Type":16,"Body":"<foo>bar</foo>"}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(
        value=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=42),
        type=VariantType.NodeId,
    )
    expected_json = '{"Type":17,"Body":{"Id":42}}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    # ua_variant = UAVariant(value=UAExpandedNodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value="42"), type=VariantType.ExpandedNodeId)
    # expected_json = '{"Type":18,"Body":{"Namespace":0,"IdType":0,"Value":42}}'
    # actual_json = ua_variant.json_encode()
    # assert actual_json == expected_json

    # ua_variant = UAVariant(value=UAStatusCode(0), type=VariantType.StatusCode)
    # expected_json = '{"Type":19,"Body":0}'
    # actual_json = ua_variant.json_encode()
    # assert actual_json == expected_json

    ua_variant = UAVariant(
        value=UAQualifiedName(namespace_index=1, name="foo"),
        type=VariantType.QualifiedName,
    )
    expected_json = '{"Type":20,"Body":{"Name":"foo","Uri":1}}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(
        value=UALocalizedText(locale="en", text="foo"), type=VariantType.LocalizedText
    )
    expected_json = '{"Type":21,"Body":{"Text":"foo","Locale":"en"}}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    ua_variant = UAVariant(
        value=UAExtensionObject(
            body=UAStructure(UAString("foo")),
            type_nodeid=UANodeId(namespace=0, nodeid_type=NodeIdType.NUMERIC, value=12),
        ),
        type=VariantType.ExtensionObject,
    )
    expected_json = '{"Type":22,"Body":{"TypeId":{"Id":12},"Body":"foo"}}'
    actual_json = ua_variant.json_encode()
    assert actual_json == expected_json

    # ua_variant = UAVariant(value=UADataValue(), type=VariantType.DataValue)
    # expected_json = '{"Type":23,"Body":{"Value":{"Type":0,"Body":null},"StatusCode":0,"SourceTimestamp":"1970-01-01T00:00:00Z","ServerTimestamp":"1970-01-01T00:00:00Z","SourcePicoseconds":0,"ServerPicoseconds":0}}'
    # actual_json = ua_variant.json_encode()
    # assert actual_json == expected_json

    # ua_variant = UAVariant(value=UADiagnosticInfo(), type=VariantType.DiagnosticInfo)
    # expected_json = '{"Type":24,"Body":{"EncodingMask":0,"SymbolicId":0,"NamespaceUri":0,"LocalizedText":0,"Locale":0,"AdditionalInfo":0,"InnerStatusCode":0,"InnerDiagnosticInfo":0}}'
    # actual_json = ua_variant.json_encode()
    # assert actual_json == expected_json


def test_ua_eu_information_creation_with_incorrect_values():
    with pytest.raises(TypeError):
        UAEUInformation(
            namespace_uri=42,
            unit_id=42,
            display_name="bar",
            description="bar",
        )
    with pytest.raises(TypeError):
        UAEUInformation(
            namespace_uri="www.mynamespace.com/",
            unit_id="42",
            display_name=UALocalizedText(text="bar", locale="en"),
            description=UALocalizedText(text="bar", locale="en"),
        )
    with pytest.raises(TypeError):
        UAEUInformation(
            namespace_uri="www.mynamespace.com/",
            unit_id=42,
            display_name=42,
            description=UALocalizedText(text="bar", locale="en"),
        )
    with pytest.raises(TypeError):
        UAEUInformation(
            namespace_uri="www.mynamespace.com/",
            unit_id=42,
            display_name=UALocalizedText(text="bar", locale="en"),
            description=42,
        )
    with pytest.raises(TypeError):
        UAEUInformation(
            namespace_namespace_uri="www.mynamespace.com/",
            unit_id=42,
            display_name=UALocalizedText(text="bar", locale="en"),
            description=UALocalizedText(text="bar", locale="en"),
        )


def test_ua_eu_information_creation_with_correct_values():
    ua_eu_information = UAEUInformation(
        namespace_uri="www.mynamespace.com/",
        unit_id=42,
        display_name=UALocalizedText(text="bar", locale="en"),
        description=UALocalizedText(text="bar", locale="en"),
    )
    assert ua_eu_information.namespace_uri == "www.mynamespace.com/"
    assert ua_eu_information.unit_id == 42
    assert ua_eu_information.display_name == UALocalizedText(text="bar", locale="en")
    assert ua_eu_information.description == UALocalizedText(text="bar", locale="en")


def test_ua_eu_information_creation_with_empty_description():
    expected_namespace_uri = "www.mynamespace.com/"
    expected_unit_id = 42
    expected_display_name = UALocalizedText(text="bar", locale="en")
    ua_eu_information = UAEUInformation(
        namespace_uri=expected_namespace_uri,
        unit_id=expected_unit_id,
        display_name=expected_display_name,
        description=pd.NA,
    )
    assert ua_eu_information.namespace_uri == expected_namespace_uri
    assert ua_eu_information.unit_id == expected_unit_id
    assert ua_eu_information.display_name == expected_display_name
    assert isinstance(ua_eu_information.description, pd._libs.missing.NAType)


def test_ua_eu_information_xml_encode():
    ua_eu_information = UAEUInformation(
        namespace_uri="www.mynamespace.com/",
        unit_id=42,
        display_name=UALocalizedText(text="bar", locale="en"),
        description=UALocalizedText(text="bar", locale="en"),
    )
    actual_xml = ua_eu_information.xml_encode(include_xmlns=False)
    expected_xml = "<EUInformation><NamespaceUri>www.mynamespace.com/</NamespaceUri><UnitId>42</UnitId><DisplayName><Locale>en</Locale><Text>bar</Text></DisplayName><Description><Locale>en</Locale><Text>bar</Text></Description></EUInformation>"
    assert actual_xml == expected_xml


def test_ua_eu_information_xml_encode_with_xmlns():
    ua_eu_information = UAEUInformation(
        namespace_uri="www.mynamespace.com/",
        unit_id=42,
        display_name=UALocalizedText(text="bar", locale="en"),
        description=UALocalizedText(text="bar", locale="en"),
    )
    actual_xml = ua_eu_information.xml_encode(include_xmlns=True)
    expected_xml = '<EUInformation xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><NamespaceUri>www.mynamespace.com/</NamespaceUri><UnitId>42</UnitId><DisplayName><Locale>en</Locale><Text>bar</Text></DisplayName><Description><Locale>en</Locale><Text>bar</Text></Description></EUInformation>'
    assert actual_xml == expected_xml


def test_ua_eu_information_json_encode():
    ua_eu_information = UAEUInformation(
        namespace_uri="www.mynamespace.com/",
        unit_id=42,
        display_name=UALocalizedText(text="bar", locale="en"),
        description=UALocalizedText(text="bar", locale="en"),
    )
    actual_json = ua_eu_information.json_encode()
    expected_json = '{"DisplayName":{"Text":"bar","Locale":"en"},"Description":{"Text":"bar","Locale":"en"},"UnitId":42,"NamespaceUri":"www.mynamespace.com/"}'
    assert actual_json == expected_json


def test_ua_engineering_units_creation_with_incorrect_values():
    # Incorrect display name type
    with pytest.raises(TypeError):
        UAEngineeringUnits(
            display_name=42,
            description="bar",
            unit_id=42,
            namespace_uri="www.mynamespace.com/",
        )
    # Incorrect description type
    with pytest.raises(TypeError):
        UAEngineeringUnits(
            display_name="bar",
            description=42,
            unit_id=42,
            namespace_uri="www.mynamespace.com/",
        )
    # Incorrect unit id type
    with pytest.raises(TypeError):
        UAEngineeringUnits(
            display_name="bar",
            description="bar",
            unit_id="42",
            namespace_uri="www.mynamespace.com/",
        )
    # Incorrect namespace uri type
    with pytest.raises(TypeError):
        UAEngineeringUnits(
            display_name="bar",
            description="bar",
            unit_id=42,
            namespace_uri=42,
        )


def test_ua_engineering_units_creation_with_correct_values():
    ua_engineering_units = UAEngineeringUnits(
        display_name=UALocalizedText("bar", "en"),
        description=UALocalizedText("bar", "en-US"),
        unit_id=42,
        namespace_uri="www.mynamespace.com/",
    )
    assert ua_engineering_units.ua_eu_information.display_name == UALocalizedText(
        "bar", "en"
    )
    assert ua_engineering_units.ua_eu_information.description == UALocalizedText(
        "bar", "en-US"
    )
    assert ua_engineering_units.ua_eu_information.unit_id == 42
    assert (
        ua_engineering_units.ua_eu_information.namespace_uri == "www.mynamespace.com/"
    )


def test_ua_engineering_units_xml_encode_with_value():
    ua_engineering_units = UAEngineeringUnits(
        display_name=UALocalizedText("bar", "en"),
        description=UALocalizedText("bar", "en-US"),
        unit_id=42,
        namespace_uri="www.mynamespace.com/",
    )
    expected_xml = "<ExtensionObject><TypeId><Identifier>i=888</Identifier></TypeId><Body><EUInformation><NamespaceUri>www.mynamespace.com/</NamespaceUri><UnitId>42</UnitId><DisplayName><Locale>en</Locale><Text>bar</Text></DisplayName><Description><Locale>en-US</Locale><Text>bar</Text></Description></EUInformation></Body></ExtensionObject>"
    actual_xml = ua_engineering_units.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    expected_xml = '<ExtensionObject xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><TypeId><Identifier>i=888</Identifier></TypeId><Body><EUInformation><NamespaceUri>www.mynamespace.com/</NamespaceUri><UnitId>42</UnitId><DisplayName><Locale>en</Locale><Text>bar</Text></DisplayName><Description><Locale>en-US</Locale><Text>bar</Text></Description></EUInformation></Body></ExtensionObject>'
    actual_xml = ua_engineering_units.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_engineering_units_json_encode_with_value():
    ua_engineering_units = UAEngineeringUnits(
        display_name=UALocalizedText("bar", "en"),
        description=UALocalizedText("bar", "en-US"),
        unit_id=42,
        namespace_uri="www.mynamespace.com/",
    )
    expected_json = '{"TypeId":{"Id":888},"Body":{"DisplayName":{"Text":"bar","Locale":"en"},"Description":{"Text":"bar","Locale":"en-US"},"UnitId":42,"NamespaceUri":"www.mynamespace.com/"}}'
    actual_json = ua_engineering_units.json_encode()
    assert actual_json == expected_json


def test_ua_range_creation_with_incorrect_values():
    with pytest.raises(TypeError):
        UARange(low="foo", high=100)
    with pytest.raises(TypeError):
        UARange(low=0, high="foo")
    with pytest.raises(ValueError):
        UARange(low=100, high=0)


def test_ua_range_creation_with_correct_values():
    ua_range = UARange(low=0, high=100)
    assert ua_range.low == 0
    assert ua_range.high == 100


def test_ua_range_xml_encode_with_value():
    ua_range = UARange(low=0, high=100)
    expected_xml = "<Range><Low>0.0</Low><High>100.0</High></Range>"
    actual_xml = ua_range.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    expected_xml = '<Range xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><Low>0.0</Low><High>100.0</High></Range>'
    actual_xml = ua_range.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_range_json_encode_with_value():
    ua_range = UARange(low=0, high=100)
    expected_json = '{"Low":0.0,"High":100.0}'
    actual_json = ua_range.json_encode()
    assert actual_json == expected_json


def test_ua_eurange_creation_with_incorrect_values():
    with pytest.raises(TypeError):
        UAEURange(low="foo", high=100)
    with pytest.raises(TypeError):
        UAEURange(low=0, high="foo")
    with pytest.raises(ValueError):
        UAEURange(low=100, high=0)


def test_ua_eurange_creation_with_correct_values():
    ua_eurange = UAEURange(low=0, high=100)
    assert ua_eurange.ua_range.low == 0
    assert ua_eurange.ua_range.high == 100


def test_ua_eurange_xml_encode():
    ua_eurange = UAEURange(low=0, high=100)
    expected_xml = "<ExtensionObject><TypeId><Identifier>i=885</Identifier></TypeId><Body><Range><Low>0.0</Low><High>100.0</High></Range></Body></ExtensionObject>"
    actual_xml = ua_eurange.xml_encode(include_xmlns=False)
    assert actual_xml == expected_xml

    expected_xml = '<ExtensionObject xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><TypeId><Identifier>i=885</Identifier></TypeId><Body><Range><Low>0.0</Low><High>100.0</High></Range></Body></ExtensionObject>'
    actual_xml = ua_eurange.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_eurange_json_encode_with_value():
    ua_eurange = UAEURange(low=0, high=100)
    expected_json = '{"TypeId":{"Id":885},"Body":{"Low":0.0,"High":100.0}}'
    actual_json = ua_eurange.json_encode()
    assert actual_json == expected_json


def test_ua_list_of_xml_encode_works_with_tuple():
    ua_list_of = UAListOf(
        value=(
            UALocalizedText(text="Disabled", locale="en-US"),
            UALocalizedText(text="Paused", locale="en"),
            UALocalizedText(text="Operational"),
            UALocalizedText(text="Error"),
        ),
        typename="UALocalizedText",
    )
    expected_xml = '<ListOfUALocalizedText  xmlns="http://opcfoundation.org/UA/2008/02/Types.xsd"><LocalizedText><Locale>en-US</Locale><Text>Disabled</Text></LocalizedText><LocalizedText><Locale>en</Locale><Text>Paused</Text></LocalizedText><LocalizedText><Locale></Locale><Text>Operational</Text></LocalizedText><LocalizedText><Locale></Locale><Text>Error</Text></LocalizedText></ListOfUALocalizedText>'
    actual_xml = ua_list_of.xml_encode(include_xmlns=True)
    assert actual_xml == expected_xml


def test_ua_list_of_raises_type_error_when_value_is_not_tuple():
    with pytest.raises(TypeError):
        UAListOf(
            value=[
                UALocalizedText(text="Disabled", locale="en-US"),
                UALocalizedText(text="Paused", locale="en"),
                UALocalizedText(text="Operational"),
                UALocalizedText(text="Error"),
            ],
            typename="UALocalizedText",
        )


def test_ua_list_of_raises_value_error_when_no_values_given():
    with pytest.raises(ValueError):
        UAListOf(value=(), typename="UALocalizedText")


def test_ua_list_of_raises_type_error_when_invalid_value_given():
    with pytest.raises(TypeError):
        UAListOf(value=3000, typename="UALocalizedText")

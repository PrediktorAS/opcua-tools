import re

from opcua_tools import nodeset_generator, ua_models


def test_required_models_are_parsed_to_xml():
    model = ua_models.UAModel(
        model_uri="http://opcfoundation.org/UA/IEC61850-6",
        publication_date="2018-02-05T00:00:00Z",
        version="2.0",
        required_models=[
            ua_models.UARequiredModel(
                model_uri="http://opcfoundation.org/UA/IEC61850-7-3",
                publication_date="2023-01-01T00:00:00Z",
                version="2.0",
            ),
            ua_models.UARequiredModel(
                model_uri="http://opcfoundation.org/UA/",
                publication_date="2019-05-01T00:00:00Z",
                version="1.04",
            ),
        ],
    )

    required_models_xml = nodeset_generator.create_required_models(model)

    assert (
        required_models_xml
        == """
        <RequiredModel ModelUri="{}" Version="{}" PublicationDate="{}" />
        <RequiredModel ModelUri="{}" Version="{}" PublicationDate="{}" />
    """.format(
            model.required_models[0].model_uri,
            model.required_models[0].version,
            model.required_models[0].publication_date,
            model.required_models[1].model_uri,
            model.required_models[1].version,
            model.required_models[1].publication_date,
        )
    )


def test_required_models_are_parsed_when_no_publication_date_given():
    model = ua_models.UAModel(
        model_uri="http://opcfoundation.org/UA/IEC61850-6",
        publication_date="2018-02-05T00:00:00Z",
        version="2.0",
        required_models=[
            ua_models.UARequiredModel(
                model_uri="http://opcfoundation.org/UA/IEC61850-7-3",
                publication_date=None,
                version="2.0",
            ),
        ],
    )

    required_models_xml = nodeset_generator.create_required_models(model)
    xml_tag_date_pattern = re.compile(r'PublicationDate="\d+-\d+-\d+')
    match_object = xml_tag_date_pattern.search(required_models_xml)

    assert match_object is not None

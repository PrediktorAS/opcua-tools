import re

from opcua_tools import nodeset_generator, ua_models


def test_required_models_are_parsed_to_xml():
    first_model = ua_models.UAModel(
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
    second_model = ua_models.UAModel(
        model_uri="http://opcfoundation.org/UA/",
        publication_date="2021-01-21T00:00:00Z",
        version="1.04.9",
        required_models=[],
    )
    models = [first_model, second_model]

    model_uri = first_model.model_uri
    required_models_xml = nodeset_generator.create_required_models(models, model_uri)

    assert (
        required_models_xml
        == """
        <RequiredModel ModelUri="{}" Version="{}" PublicationDate="{}" />
        <RequiredModel ModelUri="{}" Version="{}" PublicationDate="{}" />
    """.format(
            first_model.required_models[0].model_uri,
            first_model.required_models[0].version,
            first_model.required_models[0].publication_date,
            first_model.required_models[1].model_uri,
            first_model.required_models[1].version,
            first_model.required_models[1].publication_date,
        )
    )


def test_required_models_are_parsed_when_no_publication_date_given():
    first_model = ua_models.UAModel(
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

    model_uri = first_model.model_uri
    required_models_xml = nodeset_generator.create_required_models(
        [first_model], model_uri
    )
    xml_tag_date_pattern = re.compile(r'PublicationDate="\d+-\d+-\d+')
    match_object = xml_tag_date_pattern.search(required_models_xml)

    assert match_object is not None

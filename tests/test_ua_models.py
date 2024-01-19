from opcua_tools import ua_models


def test_ensure_that_required_models_are_hashable():
    required_models_set = set()
    required_model = ua_models.UARequiredModel(
        model_uri="http://opcfoundation.org/UA/IEC61850-7-3",
        publication_date="2023-01-01T00:00:00Z",
        version="2.0",
    )

    required_models_set.add(required_model)

    assert len(required_models_set) == 1
